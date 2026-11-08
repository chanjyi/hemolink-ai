"""Train, evaluate and save every HemoLink model, then write docs/MODEL_REPORT.md.

    python scripts/train_models.py            # all regions × blood groups (≈ 2–4 minutes)
    python scripts/train_models.py --quick    # national series only (≈ 20 seconds)

Outputs
  models/forecast/<region>__<group>.json   forecast + cross-validation results (the app serves these directly)
  models/forecast/<region>__<group>.joblib the fitted Random Forest, when it was the chosen method
  models/return_model.joblib               donor-return logistic regression (fitted on all donors)
  models/metrics.json                      every metric in one file (shown on the AI Models page)
  docs/MODEL_REPORT.md                     human-readable model report for judges / reviewers
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import joblib  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402

import forecast as F  # noqa: E402


def train_forecasts(quick: bool) -> list[dict]:
    f = F.data_file()
    if not f:
        print("! Official MOH data not found in data/. Run:  python scripts/download_data.py")
        print("  Continuing with synthetic demonstration series.")
    out_dir = F.MODEL_DIR / "forecast"
    out_dir.mkdir(parents=True, exist_ok=True)
    regions = ["Malaysia"] if quick and "Malaysia" in F.regions() else F.regions()
    results = []
    for region in regions:
        for group in F.GROUPS:
            t = time.time()
            try:
                raw, source, official = F.load_series(region, group)
                fit = F.fit_forecast(raw, folds=8 if official else 4)
            except ValueError as exc:
                print(f"  - {region} / {group}: skipped ({exc})")
                continue
            m = fit["metrics"]
            hist = raw.dropna(subset=["donations"]).tail(28)
            result = {
                "region": region, "blood_type": group, "source": source, "official": official,
                "source_last_date": fit["last"].isoformat(),
                "history": [{"date": d.date().isoformat(), "donations": int(v)} for d, v in zip(hist.date, hist.donations)],
                "future": fit["future"], "metrics": m,
                "model": m["selected_label"] + " — chosen by cross-validation",
                "trained": datetime.now().isoformat(timespec="minutes"),
                "warning": "This predicts historical-pattern donation counts, not patient needs, medical risk, or "
                           "hospital inventory. Not for clinical use.",
            }
            name = f"{region}__{group}".replace(" ", "_").replace("/", "-")
            payload = {"result": result}
            if f:
                payload.update(data_name=f.name, data_size=f.stat().st_size)
            (out_dir / f"{name}.json").write_text(json.dumps(payload))
            if m["selected"] == "rf":
                joblib.dump(F.train_rf(raw, 65), out_dir / f"{name}.joblib", compress=3)
            results.append({"region": region, "group": group, "selected": m["selected"], "mae": m["mae"],
                            "baseline_mae": m["baseline_mae"], "candidates": m["candidates"], "folds": m["test_samples"] // 7,
                            "official": official, "last": result["source_last_date"]})
            print(f"  ✓ {region:<18} {group:<4} → {m['selected']:<15} MAE {m['mae']:>7} (naive {m['baseline_mae']})  "
                  f"{time.time() - t:.1f}s")
    return results


def train_app_models() -> dict:
    """Stock outlook, donor return and matching — trained on the app's (simulated) database."""
    import app as A  # creates / seeds the database if needed
    from ai import churn
    from ai.evaluation import evaluate_all
    from ai_routes import load_centres, load_people, outlook

    with A.connect() as db:
        types = outlook(db)
        profiles, health, _ = load_people(db)
        centres = load_centres(db)
    ev = evaluate_all(profiles, health, centres)
    # final return model on all donors (the app retrains this live; saved here for reproducibility)
    from ai.util import add_days
    today = date.today().isoformat()
    km = {p.id: churn.nearest_centre_km(p, centres) for p in profiles if p.role == "donor"}
    X, y = [], []
    for h in health:
        if h.donor_id in km and (x := churn.features(h, km[h.donor_id], add_days(today, -180))) is not None:
            X.append(x)
            y.append(1 if any(add_days(today, -180) < d <= today for d in h.donations) else 0)
    model = LogisticRegression(C=1.0, max_iter=1000).fit(np.array(X), np.array(y))
    joblib.dump({"model": model, "features": churn.FEATURE_NAMES}, F.MODEL_DIR / "return_model.joblib")
    stock = [{"blood_type": t["blood_type"], "used": t["metrics"]["used"], "collected": t["metrics"]["collected"]}
             for t in types]
    return {"stock": stock, **ev}


def pct(x):
    return "–" if x is None else f"{x * 100:.0f}%"


def report(forecasts: list[dict], app: dict, trained: str) -> str:
    official = any(r["official"] for r in forecasts)
    wins = {m: sum(1 for r in forecasts if r["selected"] == m) for m in F.METHODS}
    better = [r for r in forecasts if r["baseline_mae"]]
    avg_gain = np.mean([(r["baseline_mae"] - r["mae"]) / r["baseline_mae"] for r in better]) if better else 0
    nat = [r for r in forecasts if r["region"] == "Malaysia"]
    L = [f"# HemoLink AI — Model report", "",
         f"Generated {trained} by `scripts/train_models.py`. Everything here is reproducible by re-running the script.", "",
         "## 1. Donation forecasting (trends page)", "",
         f"**Data:** {'Ministry of Health Malaysia — National Blood Centre daily donations (KKMNOW / data-darah-public, CC BY 4.0), latest three years per series' if official else 'synthetic demonstration series (official data not imported)'}."
         f" Last date: {forecasts[0]['last'] if forecasts else '–'}.", "",
         "**Method:** for every region × blood group, three methods compete — *same weekday last week* (seasonal naive), "
         "*average of the last 4 same weekdays*, and a *Random Forest* (calendar + lag features, 7-day recursive). "
         "They are compared with **rolling-origin cross-validation** (the series is cut at 8 past dates; each method "
         "forecasts the next 7 days blind). The lowest mean absolute error wins; within 2 % the simpler method wins.", "",
         f"**Result:** {len(forecasts)} series. Chosen: Random Forest {wins['rf']}, weekday average {wins['weekday_mean']}, "
         f"seasonal naive {wins['seasonal_naive']}. On average the chosen method's error is **{avg_gain * 100:.0f}% lower** "
         "than the seasonal-naive baseline.", "",
         "| Series | Chosen | MAE (chosen) | Seasonal naive | Weekday avg | Random Forest |", "|---|---|---|---|---|---|"]
    for r in (nat + [r for r in forecasts if r["region"] != "Malaysia"])[:25]:
        c = r["candidates"]
        L.append(f"| {r['region']} · {r['group']} | {F.METHODS[r['selected']].split(' (')[0]} | **{r['mae']}** | "
                 f"{c.get('seasonal_naive', '–')} | {c.get('weekday_mean', '–')} | {c.get('rf', '–')} |")
    if len(forecasts) > 25:
        L.append(f"| … {len(forecasts) - 25} more series in `models/metrics.json` | | | | | |")
    L += ["", "MAE = mean absolute error in donations per day over 7-day forecasts. Counts only — not patient demand.", "",
          "## 2. Shortage outlook (blood bank stock)", "",
          "**Data:** 180 days of SIMULATED collected / used units per blood type (no public dataset of hospital usage "
          "exists). Same three-method selection, 4 cut-off dates × 7 days. Rare types usually pick a simple method — "
          "their daily counts are too small for a Random Forest to help.", "",
          "| Type | Used → chosen (MAE) | Collected → chosen (MAE) |", "|---|---|---|"]
    for s in app["stock"]:
        L.append(f"| {s['blood_type']} | {s['used']['selected']} ({s['used']['mae']}) | "
                 f"{s['collected']['selected']} ({s['collected']['mae']}) |")
    r = app["return_model"]
    L += ["", "## 3. Donor return prediction", ""]
    if r.get("available"):
        L += [f"Logistic regression on 4 features (years since last donation, donations in the prior 2 years, no-shows, "
              f"distance to nearest centre); label = donated again within 180 days. **Simulated donors (n = {r['n']}).**", "",
              f"* 5-fold cross-validation: **AUC {r['auc']} ± {r['auc_sd']}**, accuracy {pct(r['accuracy'])} "
              f"(base rate {pct(r['base_rate'])})",
              f"* Brier score {r['brier']} vs {r['brier_baseline']} for always predicting the base rate (lower is better)", "",
              "**Calibration** (out-of-fold):", "", "| Predicted bin | Donors | Mean predicted | Actual |", "|---|---|---|---|"]
        L += [f"| {c['bin']} | {c['n']} | {pct(c['predicted'])} | {pct(c['actual'])} |" for c in r["calibration"]]
        L += ["", "**Fairness — by age band:**", "", "| Age | n | Actual | Predicted | AUC |", "|---|---|---|---|---|"]
        L += [f"| {g['group']} | {g['n']} | {pct(g['actual_rate'])} | {pct(g['predicted_rate'])} | {g['auc'] or '–'} |"
              for g in r["by_age"]]
        L += ["", "Flags (|predicted − actual| ≥ 10 points, n ≥ 15): " + (", ".join(r["flags"]) or "none") + "."]
    m = app["matching"]
    L += ["", "## 4. Donor matching fairness", "",
          f"An urgent request ({m['units_per_request']} units) was simulated for every blood type at every centre "
          f"({m['requests_simulated']} requests). Selection rate = alerted ÷ eligible compatible donors.", "",
          "| Age band | Eligible | Selected | Rate | vs best | Avg km | Avg donations |", "|---|---|---|---|---|---|---|"]
    L += [f"| {g['group']} | {g['eligible']} | {g['selected']} | {pct(g['rate'])} | {g['ratio']}{' ⚠️' if g['flag'] else ''} | "
          f"{g['avg_km']} | {g['avg_donations']} |" for g in m["by_age"]]
    L += ["", f"**Finding:** {m['explanation']}", "", f"_{m['note']}_", "",
          "## 5. Limitations", "",
          "* Stock, donors, alerts and replies are simulated; only the donation trends use real MOH data.",
          "* Forecasts predict donation counts from past patterns — not patient need, and not for clinical use.",
          "* Fairness checks use age band and area only (the app stores no gender or ethnicity).",
          "* Clinical rules (eligibility, HemoScan, medicine waiting periods) are placeholders pending clinician review.", ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true", help="national series only")
    args = ap.parse_args()
    F.MODEL_DIR.mkdir(exist_ok=True)
    trained = datetime.now().isoformat(timespec="minutes")
    print("1/2 Donation forecasts (official data when present)…")
    forecasts = train_forecasts(args.quick)
    print("2/2 Stock outlook, donor return model, matching fairness…")
    app = train_app_models()
    metrics = {"trained": trained, "data_file": F.data_file().name if F.data_file() else None,
               "forecasts": forecasts, **app}
    (F.MODEL_DIR / "metrics.json").write_text(json.dumps(metrics, indent=1, default=str))
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "MODEL_REPORT.md").write_text(report(forecasts, app, trained), encoding="utf-8")
    print(f"\nSaved models/ and docs/MODEL_REPORT.md ({len(forecasts)} forecast series).")


if __name__ == "__main__":
    main()
