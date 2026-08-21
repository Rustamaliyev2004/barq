# barq

**48-hour output and curtailment-risk forecasting for Uzbekistan's utility-scale solar and wind fleet.**

Live demo: [barq-energy.streamlit.app](https://barq-energy.streamlit.app)

---

## The problem

Uzbekistan has built 5.6 GW of utility-scale solar and wind across 21 plants. Plant operators know
what the weather will do. What they cannot see is how much of their output the grid will actually
accept — and curtailed energy is unpaid energy.

barq forecasts both, 48 hours ahead, per plant:

1. **How much a plant will generate**, hour by hour.
2. **How likely that output is to be curtailed**, given the state of the system.

## Scope of this demo

The dashboard currently runs the **six largest plants** — Sherabad, Nur Bukhara, Samarkand and
Nur Navoi Solar, plus Zarafshan and Bash Wind — which together account for just over 2 GW.
The models are fleet-agnostic: extending to all 21 plants is a matter of adding coordinates and
nameplate capacity, not retraining. Plants are added as verified capacity and location data is
confirmed.

## How it works

Three gradient-boosting models, all trained on German grid data and applied to Uzbek plants
through a residual-load scaling.

| Model | Type | Target |
|---|---|---|
| Solar | `HistGradientBoostingRegressor` | Hourly solar generation |
| Wind | `HistGradientBoostingRegressor` | Hourly wind generation |
| Curtailment | `HistGradientBoostingClassifier` | Probability of a curtailment hour |

**Features:** shortwave radiation, 2 m temperature, cloud cover, 100 m wind speed, hour, month,
day of year. The curtailment classifier adds residual load — demand minus modelled renewable
output — which is what actually drives curtailment decisions.

**Weather source:** [Open-Meteo](https://open-meteo.com) — ERA5 archive for training, forecast API
for the live 48-hour outlook.

## Why German data

Uzbekistan does not publish hourly plant-level generation or curtailment actuals. Germany does,
through ENTSO-E and SMARD, at scale and with a comparable renewable share.

Training on Germany means the accuracy figures below are **measured against published actuals**,
not asserted. The trade-off is that Uzbek output is scaled from a German-trained model pending
local calibration — which is exactly what a pilot with one operator would resolve.

## Validation

Trained on 2020–2023. Tested on **2024, a year the model never saw.**

| Metric | Result | vs. naive baseline |
|---|---|---|
| Solar forecast error | 3.7% of peak | 79% better |
| Wind forecast error | 7.4% of peak | 57% better |
| Curtailment detection | ROC AUC 0.973 | catches 72% of events |

Reproduce it yourself — `src/train.py` prints every number above, including the full
precision/recall sweep across alert thresholds.

## Repository

```
app.py                  Streamlit dashboard — the live MVP
src/get_weather.py      Pulls ERA5 hourly weather for the German fleet
src/build_dataset.py    Joins weather with ENTSO-E generation, load and price data
src/train.py            Trains all three models, prints validation, writes models.pkl
data/models.pkl         Trained models used by the app
requirements.txt        Dependencies
```

Raw ENTSO-E CSVs and the built parquet files are gitignored for size. Regenerate them by running
`src/get_weather.py` then `src/build_dataset.py`.

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

To retrain from scratch:

```bash
python src/get_weather.py      # fetches ERA5 archive, 2020-2024
python src/build_dataset.py    # builds data/training.parquet
python src/train.py            # trains and validates, writes data/models.pkl
```

## Status

Working demo. Uzbek plant coordinates and capacities are public data; output is scaled from a
German-trained model. The next step is calibration against real generation data from one Uzbek
operator — at which point the accuracy figures become Uzbek figures rather than German ones.

## Team

Built by a five-person team at New Uzbekistan University, with plant and grid domain input from
Toshkent Metropoliteni and CitiFuel.

Contact: d.rustamaliyev@newuu.uz
