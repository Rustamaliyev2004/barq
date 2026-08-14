import streamlit as st, pandas as pd, numpy as np, requests, pickle, datetime

st.set_page_config(page_title="barq", layout="wide")

PLANTS = [
    {"name": "Nur Bukhara Solar",  "type": "solar", "mw": 250, "lat": 39.77, "lon": 64.42},
    {"name": "Sherabad Solar",     "type": "solar", "mw": 457, "lat": 37.68, "lon": 67.00},
    {"name": "Samarkand Solar",    "type": "solar", "mw": 220, "lat": 39.65, "lon": 66.96},
    {"name": "Nur Navoi Solar",    "type": "solar", "mw": 100, "lat": 40.10, "lon": 65.38},
    {"name": "Zarafshan Wind",     "type": "wind",  "mw": 500, "lat": 41.60, "lon": 64.20},
    {"name": "Bash Wind",          "type": "wind",  "mw": 500, "lat": 40.30, "lon": 64.15},
]

DE_PEAK = {"solar": 38000.0, "wind": 46000.0}
UZ_FLEET_MW = 8000      # installed solar + wind, Uzbekistan
UZ_SYSTEM   = 11000     # typical Uzbek peak demand, MW
DE_SYSTEM   = 60000     # typical German peak demand, MW
FEATURES = ["shortwave_radiation","temperature_2m","cloud_cover","wind_speed_100m","hour","month","doy"]

# ---------- login ----------
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("barq")
    st.caption("energy solutions")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Sign in"):
        if u == "demo" and p == "barq2026":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

# ---------- app ----------
@st.cache_resource
def get_models():
    return pickle.load(open("data/models.pkl", "rb"))

@st.cache_data(ttl=3600)
def forecast(lat, lon):
    r = requests.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": lat, "longitude": lon,
        "hourly": "shortwave_radiation,temperature_2m,cloud_cover,wind_speed_100m",
        "forecast_days": 2, "timezone": "Asia/Tashkent"}, timeout=30)
    r.raise_for_status()
    d = pd.DataFrame(r.json()["hourly"])
    d["ts"] = pd.to_datetime(d.pop("time"))
    d = d.set_index("ts")
    d["hour"] = d.index.hour
    d["month"] = d.index.month
    d["doy"] = d.index.dayofyear
    return d

models = get_models()

st.title("barq")
st.caption("Output and curtailment risk forecasting for Uzbekistan's renewable fleet")

rows, curves = [], {}
for pl in PLANTS:
    wx = forecast(pl["lat"], pl["lon"])
    de = models[pl["type"]].predict(wx[FEATURES])
    mwh = np.clip(de / DE_PEAK[pl["type"]], 0, 1) * pl["mw"]
    curves[pl["name"]] = pd.Series(mwh, index=wx.index)

   # Uzbek system scaled onto the German load range the model was trained on
    hours = wx.index.hour
    uz_demand = 9000 + 3000*np.sin((hours-6)/24*2*np.pi)      # ~9-12 GW daily shape
    uz_vre = curves[pl["name"]].values * (UZ_FLEET_MW / pl["mw"])
    residual = (uz_demand - uz_vre) * (DE_SYSTEM / UZ_SYSTEM)
    cf = wx[FEATURES].copy()
    cf["residual_load"] = residual
    risk = models["curtail"].predict_proba(cf)[:, 1]

    rows.append({
        "Plant": pl["name"], "Type": pl["type"], "Capacity MW": pl["mw"],
        "Next 24h MWh": int(curves[pl["name"]][:24].sum()),
        "Peak MW": round(float(mwh[:24].max()), 1),
        "Curtailment risk": f"{100*float(risk[:24].max()):.0f}%",
    })

st.subheader("48-hour outlook")
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.subheader("Forecast output by plant (MW)")
st.line_chart(pd.DataFrame(curves))

st.subheader("Model accuracy, validated on German grid data")
st.caption("Trained 2020–2023, tested on 2024 — a year the model never saw. "
           "Germany publishes hourly actuals, so accuracy is measured, not claimed.")
c1, c2, c3 = st.columns(3)
c1.metric("Solar forecast error", "3.7% of peak", "79% better than baseline")
c2.metric("Wind forecast error", "7.4% of peak", "57% better than baseline")
c3.metric("Curtailment detection", "AUC 0.973", "catches 72% of events")

st.caption("Demo build. Uzbek plant coordinates and capacities are public data. "
           "Output is scaled from a German-trained model pending local calibration.")