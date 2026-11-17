"""Chronological GEFCom2014 solar benchmark using supplied weather forecasts."""
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.isotonic import IsotonicRegression
from threadpoolctl import threadpool_limits

from forecast_metrics import summarize, skill_interval

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/benchmark"


def features(data):
    data = data.sort_values("TIMESTAMP").copy()
    time = pd.to_datetime(data.TIMESTAMP)
    # GEFCom daily forecast blocks end at 00:00 the following day.
    block = (time - pd.Timedelta(hours=1)).dt.normalize()
    x = data.filter(regex="^VAR").copy()
    for column in ["VAR169", "VAR175", "VAR178", "VAR228"]:
        increment = data.groupby(block)[column].diff()
        first = data.groupby(block).cumcount().eq(0)
        increment.loc[first] = data.loc[first, column]
        x[column] = increment.clip(lower=0)
    x["hour"] = time.dt.hour
    x["month"] = time.dt.month
    x["season_sin"] = np.sin(time.dt.dayofyear * 2 * np.pi / 365.25)
    x["season_cos"] = np.cos(time.dt.dayofyear * 2 * np.pi / 365.25)
    return data, x, block


def run():
    source = pd.read_csv(OUT / "solar.csv")
    if source.duplicated(["ZONEID", "TIMESTAMP"]).any():
        raise ValueError("Duplicate zone timestamps")
    if not source.POWER.between(0, 1.05).all():
        raise ValueError("Unexpected normalized power outside [0,1.05]")
    # Preserve the source's one 1.00355 observation in evaluation.
    results, summaries, fitted = [], [], {}
    for zone, data in source.groupby("ZONEID"):
        data, x, block = features(data)
        train = block.lt("2013-07-01")
        calibration = block.ge("2013-07-01") & block.lt("2013-10-01")
        test = block.ge("2013-10-01")
        y = data.POWER
        models = []
        for quantile in [.1, .5, .9]:
            model = HistGradientBoostingRegressor(
                loss="quantile", quantile=quantile, max_iter=180,
                max_leaf_nodes=15, learning_rate=.05, l2_regularization=3,
                early_stopping=False, random_state=42,
            )
            model.fit(x[train], y[train])
            models.append(model)
        cal = np.sort(np.column_stack([m.predict(x[calibration]) for m in models]), axis=1).clip(0, 1)
        pred = np.sort(np.column_stack([m.predict(x[test]) for m in models]), axis=1).clip(0, 1)
        scores = np.maximum(cal[:, 0]-y[calibration], y[calibration]-cal[:, 2])
        level = min(1., np.ceil((len(scores)+1)*.8)/len(scores))
        correction = max(0., float(np.quantile(scores, level, method="higher")))
        lower = (pred[:, 0]-correction).clip(0,1)
        upper = (pred[:, 2]+correction).clip(0,1)
        curve = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1)
        curve.fit(x.loc[train,"VAR169"], y[train])
        base = curve.predict(x.loc[test,"VAR169"])
        residual = y[calibration]-curve.predict(x.loc[calibration,"VAR169"])
        base_low, base_high = np.quantile(residual,[.1,.9])
        climate = pd.DataFrame({"hour":x.loc[train,"hour"], "month":x.loc[train,"month"],"power":y[train]})
        climate = climate.groupby(["month","hour"]).power.median()
        climate_pred = [climate.loc[(m,h)] for m,h in zip(x.loc[test,"month"],x.loc[test,"hour"])]
        frame = pd.DataFrame({"time":pd.to_datetime(data.loc[test,"TIMESTAMP"]),
            "zone":int(zone),"actual":y[test],"median":pred[:,1],"lower":lower,"upper":upper,
            "radiation_curve":base,"climatology":climate_pred})
        metrics = summarize(y[test],pred[:,1],lower,upper)
        baseline = summarize(y[test],base,(base+base_low).clip(0,1),(base+base_high).clip(0,1))
        metrics.update({"zone":int(zone),"test_hours":len(frame),"curve_mae":baseline["mae"],
            "curve_pinball":baseline["mean_pinball"],"climatology_mae":float(np.mean(np.abs(y[test]-climate_pred))),
            "mae_skill":1-metrics["mae"]/baseline["mae"],
            "mae_skill_95pct":skill_interval(frame,"radiation_curve","median"),
            "interval_correction":correction})
        daylight = x.loc[test,"VAR169"].gt(0).to_numpy()
        metrics["forecast_daylight_hours"] = int(daylight.sum())
        metrics["daylight"] = summarize(y[test].to_numpy()[daylight],pred[daylight,1],lower[daylight],upper[daylight])
        metrics["daylight_curve_mae"] = float(np.abs(y[test].to_numpy()[daylight]-base[daylight]).mean())
        summaries.append(metrics)
        results.append(frame)
        fitted[int(zone)]={"models":models,"correction":correction,"features":list(x.columns)}
        print(json.dumps(metrics),flush=True)
    pd.concat(results).to_csv(OUT/"predictions.csv",index=False)
    (OUT/"metrics.json").write_text(json.dumps({"train_end":"2013-06-30","calibration_end":"2013-09-30",
        "test_start":"2013-10-01","test_end":"2014-07-01 00:00","sites":summaries},indent=2))
    with (OUT/"solar_models.pkl").open("wb") as file:
        pickle.dump(fitted,file)


if __name__ == "__main__":
    with threadpool_limits(limits=2):
        run()
