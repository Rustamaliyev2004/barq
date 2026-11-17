# Barq — team application worksheet

Research support, updated 17 November 2026. This is not a completed competition submission. The official GSC FAQ allows AI research, evaluation and editing, but requires the team's own substantive deliverable writing. Use your own reasoning and words and disclose the assistance used. Check the official template before choosing the final structure.

## The first decision to explain

Who needs tomorrow's expected solar generation, at what time, and what can they change after seeing it? Start with a plant operations team and its next-day generation schedule. Explain what you know from public rules, what you learned first-hand, and what remains a hypothesis. Operator discussions have not produced an agreement.

## Evidence available to you

- Three public GEFCom2014 solar sites; 6,552 hours per site, 19,656 site-hours in total.
- Central forecast MAE: 3.00%, 3.71% and 3.63% of capacity.
- Error reduction versus the fitted radiation curve: 49.6%, 40.7% and 34.8%.
- Other baselines: month/hour seasonal median and 48-hour persistence. The selected point model beats both on all three sites.
- Nominal 80% ranges cover only 65–68% of daylight observations. Range reliability is unfinished.
- Site 2 uses extra trees. Sites 1 and 3 use gradient boosting. No new fundamental AI architecture is claimed.
- These are small benchmark installations outside Uzbekistan. Version 2 reused dates inspected during development. Neither independent prospective validation nor utility-scale transfer is established.
- No revenue, customer contract, verified Uzbek accuracy, curtailment savings or emissions savings is demonstrated.

## Team-authored answers to prepare

1. Problem: describe one concrete scheduling task and why errors matter. Distinguish an actual operational consequence from a possible one.
2. Solution: describe inputs, central forecast, uncertainty warning, schedule comparison and the human's final decision.
3. Original contribution: explain what your team built, understands and can defend. Existing commercial solar forecasting and previous GSC forecasting projects mean AI alone is not differentiation.
4. Evidence: select a representative day, show the whole-period table, and explain the uncertainty failure. Include source attribution and evaluation limits.
5. Build plan: decide who owns weather data ingestion, model evaluation, the interface, operator research and impact measurement. Do not promise access already secured unless it is.
6. Impact: show the causal chain you intend to test: forecast → decision → measured operational change. State which links have no evidence yet.
7. Team: confirm university enrollment and roles for this competition. Do not automatically reuse Lailak's roster or equity split.
8. Disclosure: explain AI-assisted research, software development, testing and editing. Team members must review and understand the implementation and write the substantive proposal themselves.

## Proposed Build-stage acceptance checks — agree before new data

- A local operator or qualified energy professional can identify a recurring decision and a forecast delivery time. No usable decision after five substantive interviews means revisit the workflow.
- On untouched future data, compare with the existing operator forecast, a weather-to-power model, seasonal and persistence baselines. Do not keep tuning to the same evaluation dates.
- A practical initial gate could be at least 10% lower daylight MAE than the strongest available baseline. This is a proposed development target, not a contest rule or achieved local result.
- Evaluate 80% bands by season and output level. Discuss an acceptable width with the user. Do not use a lower bound as a delivery guarantee while coverage fails.
- Measure both energy below and above schedule. Add real asymmetric costs only after verifying contract terms. Stop a scheduling claim if the benefit disappears with those terms.
- Do not claim avoided emissions or curtailment without dispatch and operational evidence supporting the link.

## Submission checklist

Official details: https://www.globalsustainabilitychallenge.org/challenge-details/
Official FAQ: https://www.globalsustainabilitychallenge.org/faqs/
Portal: https://hub.globalsustainabilitychallenge.org/en/challenges/2026-27

- Confirm eligible student team and the required adult member.
- Download the actual template from the logged-in portal. It has not been inspected in this work.
- Team authors the substantive proposal and exports a PDF below 10 MB.
- Team records the required two-minute explanation, then tests its unlisted YouTube link while signed out.
- Check all application answers against EVIDENCE.md. Keep both successful and failed results.
- Deadline reported by the official guide: 22 November 2026, 23:59 UTC (23 November, 04:59 Tashkent). Submit early on November 22.
- Retain the confirmation. Nothing in this package establishes submission or acceptance.
