# Barq

A renewable generation forecasting research prototype for plant operations teams.

The app replays forecasts and actual generation for three public GEFCom2014 solar farms. It selects between gradient boosting and extra trees, compares three baselines, shows experimental uncertainty ranges, and measures energy both below and above alternative schedules. The ranges currently miss their daylight coverage target.

## Run

    pip install -r requirements.txt
    streamlit run app.py

The app loads the included benchmark results and works without a weather API. To reproduce model training, obtain the exact public CSV specified in `data/benchmark/source.txt`, save it as `data/benchmark/solar.csv`, and run:

    python src/benchmark_solar_v2.py

Training ends June 2013. July–August 2013 selects the point model. September 2013 calibrates ranges. October 2013–June 2014 is the evaluation period, already inspected during development. The point models use supplied numerical weather forecasts and calendar features. Accumulated radiation is differenced within daily forecast blocks. No future actual power is used as an input. The original source contains one normalized power value of 1.00355, which is retained in evaluation.

This is our chronological research replay, separate from the original GEFCom official competition protocol. Provenance, raw file hash and exact download revision are recorded. Confirm the dataset reuse terms before commercial distribution. The public data is an external benchmark. Uzbek site performance and financial impact require local evaluation. Calibration coverage is empirical, and temporal dependence or distribution changes can affect future coverage.

## Earlier Barq work

The legacy scripts `src/train.py`, `src/build_dataset.py` and `src/get_weather.py` remain available for tracing the earlier experiment. They used German aggregate generation, historical reanalysis weather and a negative-price classification target. Those results evaluate that historical setup. They cannot establish issue-time forecast skill, Uzbek plant performance or physical curtailment detection. The new app uses the benchmark evidence described above.

## Contest preparation

See `../research_notes/Barq forecasting competition evidence/` for source research. The team must author its substantive Global Sustainability Challenge submission and disclose significant AI assistance, following the organizer's FAQ. A proposed pilot should specify a forecast issue time, strong operational baseline, metering and curtailment flags, acceptable uncertainty width, and a prospective evaluation period.

## Current evaluation limits

Version 2 follows observation of version 1 on the same test dates. Results are exploratory. Narrow ranges miss the 80% daylight coverage target, as displayed in the app. Forecast issue times are reconstructed from the competition protocol. The CSV has no provider delivery log. The installations are small benchmark arrays. Uzbek and utility-scale performance require independent evaluation. This version improves solar evaluation and decision replay. Wind retraining is pending.
