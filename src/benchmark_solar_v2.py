"""Model selection and conditional error ranges, with chronological partitions.

The test period was inspected in v1. This revision is exploratory development;
its scores must be confirmed on an independent future dataset.
"""
import hashlib
import json
import pickle

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.isotonic import IsotonicRegression
from threadpoolctl import threadpool_limits

from benchmark_solar import OUT, features
from forecast_metrics import summarize, skill_interval

POWER_BINS = np.array([.02, .1, .25, .5, .75])


def error_ranges(observed, prediction):
    """Estimate local errors on calibration data only, retaining bin counts."""
    residual = np.asarray(observed) - prediction
    groups = np.digitize(prediction, POWER_BINS)
    ranges = []
    for group in range(len(POWER_BINS) + 1):
        sample = residual[groups == group]
        count = len(sample)
        if count < 40:
            sample = residual
        low, high = np.quantile(sample, [.1, .9])
        ranges.append({"low": min(0., float(low)), "high": max(0., float(high)), "count": count})
    return ranges


def apply_ranges(prediction, ranges):
    group = np.digitize(prediction, POWER_BINS)
    lower = np.array([ranges[i]["low"] for i in group]) + prediction
    upper = np.array([ranges[i]["high"] for i in group]) + prediction
    return lower.clip(0, 1), upper.clip(0, 1)


def run():
    source = pd.read_csv(OUT / "solar.csv")
    if source.duplicated(["ZONEID", "TIMESTAMP"]).any() or source.isna().any().any():
        raise ValueError("Unexpected duplicate or missing source values")
    summaries, results, models = [], [], {}
    for zone, data in source.groupby("ZONEID"):
        data, x, issue = features(data)
        counts = issue.value_counts()
        if not counts.eq(24).all():
            raise ValueError("Expected 24 forecast leads per issue")
        train = issue.lt("2013-07-01")
        selection = issue.ge("2013-07-01") & issue.lt("2013-09-01")
        calibration = issue.ge("2013-09-01") & issue.lt("2013-10-01")
        test = issue.ge("2013-10-01")
        y = data.POWER
        candidates = {
            "boosted_median": HistGradientBoostingRegressor(loss="quantile", quantile=.5,
                max_iter=180, max_leaf_nodes=15, learning_rate=.05, l2_regularization=3,
                early_stopping=False, random_state=42),
            "extra_trees": ExtraTreesRegressor(n_estimators=150, min_samples_leaf=8,
                max_depth=20, n_jobs=2, random_state=42),
        }
        selection_error = {}
        for name, model in candidates.items():
            model.fit(x[train], y[train])
            selection_error[name] = float(np.abs(y[selection]-model.predict(x[selection])).mean())
        winner = min(selection_error, key=selection_error.get)
        model = candidates[winner]
        cal_pred = model.predict(x[calibration]).clip(0, 1)
        central = model.predict(x[test]).clip(0, 1)
        ranges = error_ranges(y[calibration], cal_pred)
        low, high = apply_ranges(central, ranges)
        curve = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1)
        curve.fit(x.loc[train,"VAR169"], y[train])
        baseline = curve.predict(x.loc[test,"VAR169"])
        base_ranges = error_ranges(y[calibration],curve.predict(x.loc[calibration,"VAR169"]))
        base_low, base_high = apply_ranges(baseline,base_ranges)
        climate = pd.DataFrame({"hour":x.loc[train,"hour"],"month":x.loc[train,"month"],"power":y[train]})
        climate = climate.groupby(["month","hour"]).power.median()
        climate_pred = np.array([climate.loc[(m,h)] for m,h in zip(x.loc[test,"month"],x.loc[test,"hour"])])
        times = pd.to_datetime(data.TIMESTAMP)
        historical = pd.Series(y.to_numpy(),index=times)
        persistence = historical.reindex(times[test]-pd.Timedelta(hours=48)).to_numpy()
        daylight = x.loc[test,"VAR169"].gt(0).to_numpy()
        frame = pd.DataFrame({"time":times[test],"issue_time":issue[test],
            "lead_hours":((times[test]-issue[test]).dt.total_seconds()/3600).astype(int),
            "zone":int(zone),"actual":y[test],"median":central,"lower":low,"upper":high,
            "radiation_curve":baseline,"climatology":climate_pred,"persistence_48h":persistence,
            "forecast_daylight":daylight})
        metrics = summarize(y[test],central,low,high)
        base_metrics = summarize(y[test],baseline,base_low,base_high)
        metrics.update({"zone":int(zone),"selected_model":winner,"selection_mae":selection_error,
            "test_hours":len(frame),"curve_mae":base_metrics["mae"],"curve_pinball":base_metrics["mean_pinball"],
            "climatology_mae":float(np.abs(y[test]-climate_pred).mean()),
            "persistence_mae":float(np.abs(y[test]-persistence).mean()),
            "mae_skill":1-metrics["mae"]/base_metrics["mae"],
            "mae_skill_95pct":skill_interval(frame,"radiation_curve","median"),
            "daylight":summarize(y[test].to_numpy()[daylight],central[daylight],low[daylight],high[daylight]),
            "forecast_daylight_hours":int(daylight.sum()),"calibration_bins":ranges})
        # Evaluate both directions of mismatch under equal unit cost. Lower
        # schedules cannot appear beneficial simply by promising zero output.
        metrics["schedule_mismatch_per_mw"] = {
            name:float(np.abs(frame.actual-frame[name]).sum())
            for name in ["median","lower","radiation_curve","persistence_48h"]}
        summaries.append(metrics)
        results.append(frame)
        models[int(zone)] = {"model":model,"ranges":ranges,"features":list(x.columns)}
        print(json.dumps(metrics),flush=True)
    pd.concat(results).to_csv(OUT / "predictions.csv",index=False)
    report = {"version":2,"input_sha256":hashlib.sha256((OUT/"solar.csv").read_bytes()).hexdigest(),
        "train_end":"2013-06-30","selection_end":"2013-08-31","calibration_end":"2013-09-30",
        "test_start":"2013-10-01","test_end":"2014-07-01 00:00",
        "issue_time_source":"reconstructed_GEFCom_protocol",
        "evaluation_status":"Exploratory revision after inspecting v1 on the same test period",
        "sites":summaries}
    (OUT/"metrics.json").write_text(json.dumps(report,indent=2))
    with (OUT/"solar_models.pkl").open("wb") as stream:
        pickle.dump(models,stream)


if __name__ == "__main__":
    with threadpool_limits(limits=2):
        run()
