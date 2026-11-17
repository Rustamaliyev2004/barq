"""Barq renewable forecasting evidence and scheduling replay."""
import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data/benchmark'
st.set_page_config(page_title='Barq | Renewable forecasts', layout='wide')
st.markdown('''<style>
.stApp {background:#f7f8f4;color:#17362e}
h1,h2,h3 {letter-spacing:-.025em}
[data-testid="stMetric"] {background:#eaf0e8;padding:18px;border-radius:8px}
</style>''', unsafe_allow_html=True)
st.title('Barq')
st.write('Renewable generation forecasts with uncertainty you can inspect.')
st.caption('Research prototype · Three public solar sites · GEFCom2014 historical replay')
if not (DATA/'metrics.json').exists():
    st.info('The benchmark is being prepared. Run python src/benchmark_solar_v2.py to generate results.')
    st.stop()

@st.cache_data
def load_results():
    return pd.read_csv(DATA/'predictions.csv',parse_dates=['time']), json.loads((DATA/'metrics.json').read_text())

predictions, report = load_results()
zone = st.selectbox('Solar site', sorted(predictions.zone.unique()), format_func=lambda n:f'Benchmark site {n}')
frame = predictions[predictions.zone.eq(zone)].copy()
metrics = next(row for row in report['sites'] if row['zone']==zone)
a,b,c = st.columns(3)
a.metric('Error (% capacity)', f"{100*metrics['mae']:.2f}%")
b.metric('Error reduction',f"{100*metrics['mae_skill']:.1f}%")
c.metric('Range coverage',f"{100*metrics['coverage_80']:.1f}%")
st.warning(f"Experimental ranges cover {100*metrics['daylight']['coverage_80']:.1f}% of daylight observations, below the 80% target. The lower edge is a research scenario, with no guaranteed delivery level.")
st.caption(f"Error reduction compares against the radiation curve. Range coverage targets 80%. Chronological test period starts {report['test_start']}. Average range width is {100*metrics['mean_interval_width']:.1f}% of capacity. These results describe the benchmark farms.")
replay, evidence, local = st.tabs(['Forecast and schedule','Evidence','Uzbekistan pilot'])
with replay:
    st.subheader('Inspect a delivery day')
    # Forecast block runs 01:00 through the next 00:00, in dataset time.
    frame['delivery_day'] = (frame.time-pd.Timedelta(hours=1)).dt.date
    dates = sorted(frame.delivery_day.unique())
    selected = st.selectbox('Forecast day', dates, index=len(dates)//2)
    day = frame[frame.delivery_day.eq(selected)].copy()
    capacity = st.number_input('Illustrative plant capacity (MW)', min_value=1.,value=100.,step=10.)
    st.caption('The benchmark reports normalized power. The capacity control scales the replay for explanation. Dataset timestamps are retained.')
    for col in ['actual','median','lower','upper','radiation_curve']:
        day[col] *= capacity
    base = alt.Chart(day).encode(x=alt.X('time:T',title='Delivery time'))
    band = base.mark_area(color='#9abfa9',opacity=.4).encode(y=alt.Y('lower:Q',title='Power (MW)'),y2='upper:Q')
    lines = day.melt(id_vars=['time'],value_vars=['actual','median','radiation_curve'],var_name='Series',value_name='MW')
    line = alt.Chart(lines).mark_line().encode(x='time:T',y='MW:Q',color=alt.Color('Series:N',scale=alt.Scale(range=['#172e28','#16835b','#be8c42'])),tooltip=['time:T','Series:N',alt.Tooltip('MW:Q',format='.2f')])
    st.altair_chart((band+line).properties(height=340),width='stretch')
    st.write('The green band is an experimental hourly uncertainty range estimated from earlier errors. Its measured coverage appears above. Coverage can change across sites and seasons.')
    choice = st.radio('Illustrative generation schedule',['Central forecast','Lower edge of range'],horizontal=True)
    schedule = day['median'] if choice=='Central forecast' else day['lower']
    shortfall = (schedule-day.actual).clip(lower=0).sum()
    excess = (day.actual-schedule).clip(lower=0).sum()
    a,b,c = st.columns(3)
    a.metric('Scheduled energy',f'{schedule.sum():.1f} MWh')
    b.metric('Energy below schedule',f'{shortfall:.1f} MWh')
    c.metric('Energy above schedule',f'{excess:.1f} MWh')
    st.write(f"Total absolute schedule mismatch is {shortfall+excess:.1f} MWh.")
    st.caption('One-hour intervals. A lower schedule trades reduced shortfall for more energy above schedule. The replay assumes all actual output can be delivered. Payment rules, network limits and dispatch instructions require a separate study.')
    st.download_button('Download this forecast and actuals',day.to_csv(index=False),'barq_day.csv','text/csv')
with evidence:
    st.subheader('How the result was measured')
    st.write('Training uses April 2012–June 2013. July–August 2013 selects between gradient boosting and an extra-trees ensemble. September 2013 calibrates the uncertainty range. October 2013–June 2014 supplies the evaluation period. Each farm has its own models. Test output is excluded from fitting and selection. This revision follows inspection of an earlier model on the same dates, so results are exploratory and need independent confirmation.')
    st.caption('Forecast issue times are reconstructed from the GEFCom daily issue protocol. The CSV has no logged provider delivery timestamps. These small benchmark installations do not establish utility-scale or Uzbek performance.')
    st.write('The model uses the supplied numerical weather forecasts and calendar information. The point model is selected by its earlier validation error. Ranges use the 10th and 90th percentiles of calibration errors within forecast-output groups. Sparse groups use the full calibration error distribution. The radiation baseline learns a monotonic power curve from training data. The seasonal baseline uses the training median for each month and hour.')
    table=pd.DataFrame(report['sites'])[['zone','test_hours','mae','curve_mae','climatology_mae','persistence_mae','coverage_80','mean_interval_width','mean_pinball','curve_pinball']]
    st.dataframe(table,hide_index=True,width='stretch')
    interval=metrics['mae_skill_95pct']
    st.write(f"Weekly block resampling gives a 95% interval of {100*interval[0]:.1f}% to {100*interval[1]:.1f}% for error reduction against the radiation curve on this farm.")
    daylight = metrics['daylight']
    st.write(f"During hours with positive forecast radiation, error is {100*daylight['mae']:.2f}% of capacity and interval coverage is {100*daylight['coverage_80']:.1f}%. Average daytime width is {100*daylight['mean_interval_width']:.1f}% of capacity.")
    st.caption('This is our chronological replay, with three quantiles. It is not an official GEFCom competition score. Hourly coverage does not imply a joint daily guarantee. Local forecast skill and financial savings remain to be measured.')
    st.download_button('Download all test predictions',predictions.to_csv(index=False),'barq_test_predictions.csv','text/csv')
    st.markdown('[Dataset research repository](https://github.com/akylasstrat/df-forecast-comb) · [GEFCom2014 dataset description](https://github.com/greenlytics/mqe-forecast/blob/master/data/gefcom2014/README.md)')
with local:
    st.subheader('Test a generation schedule at one plant')
    st.write('The intended first user is a solar plant operations team preparing expected generation and communicating uncertainty to dispatchers. A pilot would compare Barq with the forecast that team already uses.')
    st.write('Needed inputs are time-stamped weather forecasts with their issue times, metered power, plant capacity, and outage or curtailment flags. The last two distinguish forecast error from output deliberately reduced by operations.')
    st.write('Agree the forecast delivery time, useful error reduction and acceptable range width before evaluating new dates. Report errors by season and output level, uncertainty coverage, and schedule shortfalls. The operator retains scheduling and dispatch decisions.')
    st.caption('No Uzbek pilot or customer agreement is currently established. The earlier German negative-price model was an electricity-price event classifier. Physical curtailment needs separate labels and network evidence.')
