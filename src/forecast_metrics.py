"""Metrics for normalized generation forecasts, with day-block uncertainty."""
import numpy as np


def pinball(actual, forecast, quantile):
    error = np.asarray(actual) - np.asarray(forecast)
    return float(np.maximum(quantile * error, (quantile - 1) * error).mean())


def summarize(actual, median, lower, upper):
    actual = np.asarray(actual)
    return {
        "mae": float(np.abs(actual - median).mean()),
        "rmse": float(np.sqrt(np.square(actual - median).mean())),
        "coverage_80": float(((actual >= lower) & (actual <= upper)).mean()),
        "mean_interval_width": float(np.mean(upper - lower)),
        "mean_pinball": float(np.mean([
            pinball(actual, lower, .1), pinball(actual, median, .5),
            pinball(actual, upper, .9),
        ])),
    }


def skill_interval(frame, reference, candidate, seed=42):
    """Paired calendar-week bootstrap of MAE improvement over a reference."""
    groups = frame.assign(
        reference_error=(frame.actual - frame[reference]).abs(),
        candidate_error=(frame.actual - frame[candidate]).abs(),
        week=frame.time.dt.to_period("W"),
    ).groupby("week")[["reference_error", "candidate_error"]].sum()
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(groups), size=(2000, len(groups)))
    errors = groups.to_numpy()[draws].sum(axis=1)
    skill = 1 - errors[:, 1] / np.maximum(errors[:, 0], 1e-12)
    return [float(value) for value in np.quantile(skill, [.025, .975])]
