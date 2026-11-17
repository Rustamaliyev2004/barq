# Barq benchmark evidence

Updated 17 November 2026. Version 2. Three GEFCom2014 solar sites, 19,656 site-hours across 6,552 distinct hourly timestamps. These small installations do not establish utility-scale performance.

| Site | Model MAE (% capacity) | Radiation-curve MAE | Error reduction | Daylight MAE | Daylight range coverage | Daylight width (% capacity) |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 3.00 | 5.94 | 49.6% | 5.33 | 67.9% | 19.7 |
| 2 | 3.71 | 6.26 | 40.7% | 6.59 | 65.2% | 19.8 |
| 3 | 3.63 | 5.56 | 34.8% | 6.44 | 67.1% | 19.3 |

## What improved

A reproducible plant-level forecasting experiment now uses supplied numerical weather forecasts and actual metered power. Model selection compares gradient boosting and extra trees. Three baselines are included: a radiation curve, a month/hour seasonal median, and generation 48 hours earlier. All three point models beat all three baselines on this replay. The app shows actual observations, predictions and two-sided schedule mismatch, with downloadable data.

These figures quantify error reduction against the fitted radiation baseline. They do not quantify improvement over the old German aggregate model, which used a different target and input regime. No commercial forecasting service was benchmarked. Wind was not retrained.

## Time and evaluation design

Training: April 2012–June 2013. Model selection: July–August 2013. Range calibration: September 2013. Evaluation: forecast issues October 2013–June 2014, with the last target at July 1, 00:00. Every issue has 24 target hours. Issue timestamps are reconstructed from the GEFCom protocol; the CSV has no delivery logs. Accumulated weather fields are converted to hourly increments within each daily forecast block. No future actual power enters the features.

Version 2 was developed after inspection of version 1 on the same evaluation dates. This is exploratory development, not a fresh independent final test. Weekly bootstrap intervals describe resampling uncertainty on these dates, not all sources of uncertainty. The source's one normalized reading above 1 is retained.

## Uncertainty has not passed

The nominal range target is 80%. Version 1 had 88–92% daylight coverage but widths of 42–47% of plant capacity. Version 2 narrows those widths to around 19–20%, but daylight coverage falls to 65–68%. Neither version establishes sufficiently useful operational uncertainty. Both results are retained. An independent future evaluation must assess coverage and width together, by season and output level.

The CSV field `median` is the central prediction for compatibility. Site 2 uses an extra-trees conditional-mean estimator, not a fitted median estimator. Pinball scoring at 0.5 evaluates that point forecast but does not change the estimator's objective.

## Decision and impact boundaries

The replay measures energy below and above a proposed schedule and their sum. Reducing the schedule lowers shortfall but can increase total mismatch. It assumes actual generation can be delivered and models no Uzbek network limits, PPA, penalties or revenue. Improvements in this replay are not measured curtailment, money or emissions savings.

No Uzbek customer agreement, field validation or production deployment is established. The app runs locally. Public hosting of this revision is separate from local checks. The competition application still needs confirmed student eligibility, the actual portal template, team-authored substantive proposal and recorded video.

## Reproduction

Use README.md and the pinned URL/hash in source.txt. metrics.json and predictions.csv contain full outputs. previous/metrics_v1.json preserves the earlier range results. The raw source CSV is kept locally and excluded from the distribution package; upstream reuse terms require confirmation before commercial redistribution.
