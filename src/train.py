import pandas as pd, numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.metrics import mean_absolute_error, roc_auc_score, precision_score, recall_score
import pickle

df = pd.read_parquet("data/training.parquet")

FEATURES = ["shortwave_radiation", "temperature_2m", "cloud_cover",
            "wind_speed_100m", "hour", "month", "doy"]

CURTAIL_FEATURES = FEATURES + ["residual_load"]

# train on 2020-2023, test on 2024 it has never seen
train = df[df.index.year < 2024]
test  = df[df.index.year == 2024]
print(f"train {len(train)} hours, test {len(test)} hours\n")

models = {}

for target in ["solar", "wind"]:
    m = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.08, random_state=0)
    m.fit(train[FEATURES], train[target])
    pred = m.predict(test[FEATURES])
    mae = mean_absolute_error(test[target], pred)
    baseline = mean_absolute_error(test[target], np.full(len(test), train[target].mean()))
    cap = test[target].max()
    print(f"{target.upper()}")
    print(f"  MAE            {mae:,.0f} MWh")
    print(f"  as % of peak   {100*mae/cap:.1f}%")
    print(f"  naive baseline {baseline:,.0f} MWh")
    print(f"  improvement    {100*(1-mae/baseline):.0f}%\n")
    models[target] = m

c = HistGradientBoostingClassifier(max_iter=400, learning_rate=0.08, random_state=0)
c.fit(train[CURTAIL_FEATURES], train["curtail"])
prob = c.predict_proba(test[CURTAIL_FEATURES])[:, 1]

print("CURTAILMENT RISK")
print(f"  events in test  {test['curtail'].sum()}")
print(f"  ROC AUC         {roc_auc_score(test['curtail'], prob):.3f}\n")
print("  threshold  precision  recall  alerts")
for t in [0.05, 0.10, 0.15, 0.20, 0.30, 0.50]:
    p = (prob > t).astype(int)
    print(f"  {t:>6.2f}  {precision_score(test['curtail'], p, zero_division=0):>9.2f}"
          f"  {recall_score(test['curtail'], p):>6.2f}  {p.sum():>6}")

models["curtail"] = c

pickle.dump(models, open("data/models.pkl", "wb"))
print("\nsaved data/models.pkl")