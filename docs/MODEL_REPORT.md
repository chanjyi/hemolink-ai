# HemoLink AI — Model report

Generated 2026-11-08T01:19 by `scripts/train_models.py`. Everything here is reproducible by re-running the script.

## 1. Donation forecasting (trends page)

**Data:** Ministry of Health Malaysia — National Blood Centre daily donations (KKMNOW / data-darah-public, CC BY 4.0), latest three years per series. Last date: 2026-10-28.

**Method:** for every region × blood group, three methods compete — *same weekday last week* (seasonal naive), *average of the last 4 same weekdays*, and a *Random Forest* (calendar + lag features, 7-day recursive). They are compared with **rolling-origin cross-validation** (the series is cut at 8 past dates; each method forecasts the next 7 days blind). The lowest mean absolute error wins; within 2 % the simpler method wins.

**Result:** 70 series. Chosen: Random Forest 57, weekday average 13, seasonal naive 0. On average the chosen method's error is **27% lower** than the seasonal-naive baseline.

| Series | Chosen | MAE (chosen) | Seasonal naive | Weekday avg | Random Forest |
|---|---|---|---|---|---|
| Malaysia · all | Random Forest | **163.76** | 233.86 | 198.55 | 163.76 |
| Malaysia · A | Random Forest | **44.09** | 68.61 | 54.04 | 44.09 |
| Malaysia · B | Random Forest | **47.71** | 68.04 | 57.41 | 47.71 |
| Malaysia · AB | Random Forest | **13.63** | 21.23 | 16.87 | 13.63 |
| Malaysia · O | Random Forest | **74.75** | 102.48 | 85.24 | 74.75 |
| Johor · all | Random Forest | **32.75** | 42.93 | 36.35 | 32.75 |
| Johor · A | Random Forest | **8.82** | 13.05 | 9.8 | 8.82 |
| Johor · B | Random Forest | **9.48** | 13.79 | 10.49 | 9.48 |
| Johor · AB | Random Forest | **3.1** | 4.29 | 3.65 | 3.1 |
| Johor · O | Random Forest | **15.49** | 20.59 | 17.27 | 15.49 |
| Kedah · all | Random Forest | **26.08** | 33.32 | 31.0 | 26.08 |
| Kedah · A | Random Forest | **7.95** | 9.34 | 8.14 | 7.95 |
| Kedah · B | Random Forest | **7.67** | 10.04 | 8.81 | 7.67 |
| Kedah · AB | Random Forest | **1.97** | 2.75 | 2.38 | 1.97 |
| Kedah · O | Random Forest | **12.87** | 16.34 | 14.55 | 12.87 |
| Kelantan · all | Random Forest | **28.2** | 37.39 | 30.15 | 28.2 |
| Kelantan · A | Random Forest | **7.86** | 11.27 | 8.35 | 7.86 |
| Kelantan · B | Random Forest | **7.09** | 10.16 | 8.07 | 7.09 |
| Kelantan · AB | Random Forest | **2.07** | 3.46 | 2.46 | 2.07 |
| Kelantan · O | Random Forest | **11.32** | 15.86 | 12.87 | 11.32 |
| Melaka · all | Random Forest | **35.68** | 52.32 | 43.3 | 35.68 |
| Melaka · A | Random Forest | **9.65** | 12.39 | 11.3 | 9.65 |
| Melaka · B | Random Forest | **10.71** | 15.75 | 12.77 | 10.71 |
| Melaka · AB | Random Forest | **3.18** | 5.18 | 3.71 | 3.18 |
| Melaka · O | Random Forest | **15.52** | 23.14 | 18.24 | 15.52 |
| … 45 more series in `models/metrics.json` | | | | | |

MAE = mean absolute error in donations per day over 7-day forecasts. Counts only — not patient demand.

## 2. Shortage outlook (blood bank stock)

**Data:** 180 days of SIMULATED collected / used units per blood type (no public dataset of hospital usage exists). Same three-method selection, 4 cut-off dates × 7 days. Rare types usually pick a simple method — their daily counts are too small for a Random Forest to help.

| Type | Used → chosen (MAE) | Collected → chosen (MAE) |
|---|---|---|
| O+ | weekday_mean (2.44) | rf (2.62) |
| O- | rf (0.28) | seasonal_naive (0.29) |
| A+ | rf (1.42) | rf (1.84) |
| A- | seasonal_naive (0.0) | seasonal_naive (0.0) |
| B+ | rf (1.58) | rf (1.72) |
| B- | seasonal_naive (0.0) | weekday_mean (0.06) |
| AB+ | seasonal_naive (0.36) | rf (0.5) |
| AB- | seasonal_naive (0.0) | seasonal_naive (0.0) |

## 3. Donor return prediction

Logistic regression on 4 features (years since last donation, donations in the prior 2 years, no-shows, distance to nearest centre); label = donated again within 180 days. **Simulated donors (n = 256).**

* 5-fold cross-validation: **AUC 0.845 ± 0.036**, accuracy 77% (base rate 31%)
* Brier score 0.145 vs 0.213 for always predicting the base rate (lower is better)

**Calibration** (out-of-fold):

| Predicted bin | Donors | Mean predicted | Actual |
|---|---|---|---|
| 0–20% | 105 | 5% | 2% |
| 20–40% | 47 | 29% | 26% |
| 40–60% | 65 | 51% | 65% |
| 60–80% | 39 | 68% | 59% |
| 80–100% | 0 | – | – |

**Fairness — by age band:**

| Age | n | Actual | Predicted | AUC |
|---|---|---|---|---|
| 17–24 | 23 | 26% | 29% | 0.98 |
| 25–34 | 63 | 30% | 30% | 0.834 |
| 35–44 | 74 | 30% | 30% | 0.817 |
| 45–54 | 64 | 33% | 32% | 0.827 |
| 55+ | 32 | 34% | 35% | 0.922 |

Flags (|predicted − actual| ≥ 10 points, n ≥ 15): none.

## 4. Donor matching fairness

An urgent request (4 units) was simulated for every blood type at every centre (40 requests). Selection rate = alerted ÷ eligible compatible donors.

| Age band | Eligible | Selected | Rate | vs best | Avg km | Avg donations |
|---|---|---|---|---|---|---|
| 17–24 | 428 | 97 | 23% | 1.0 | 16.5 | 1.7 |
| 25–34 | 813 | 173 | 21% | 0.94 | 16.7 | 2.2 |
| 35–44 | 1121 | 232 | 21% | 0.91 | 17.7 | 1.7 |
| 45–54 | 834 | 143 | 17% | 0.75 ⚠️ | 17.7 | 1.7 |
| 55+ | 498 | 89 | 18% | 0.79 ⚠️ | 17.2 | 1.4 |

**Finding:** Flagged: 45–54 (avg 17.7 km, 1.7 past donations), 55+ (avg 17.2 km, 1.4 past donations) vs 17–24 (avg 16.5 km, 1.7 donations). Age is not used in the score, so the gap most likely comes from factors that differ between these groups — here distance and past donations (the 'regular donor' points). Options: cap the regular-donor points, or reserve a share of alerts for first-time donors — decide with the blood bank, then re-run this check.

_Age is not a scoring factor, so age-band selection rates should be similar. Area differences mostly follow distance to the centre, which is an intended factor (shorter trips → more donors actually come). Flags use the four-fifths rule and need human review, not automatic changes._

## 5. Limitations

* Stock, donors, alerts and replies are simulated; only the donation trends use real MOH data.
* Forecasts predict donation counts from past patterns — not patient need, and not for clinical use.
* Fairness checks use age band and area only (the app stores no gender or ethnicity).
* Clinical rules (eligibility, HemoScan, medicine waiting periods) are placeholders pending clinician review.
