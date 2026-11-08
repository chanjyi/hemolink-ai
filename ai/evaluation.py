"""
Model evaluation + fairness checks (used by the AI Models page and scripts/train_models.py).

Return prediction (logistic regression):
  * 5-fold stratified cross-validation → AUC, accuracy and Brier score (mean ± sd)
  * calibration: predicted vs actual return rate in 5 bins
  * fairness: actual vs predicted rate and AUC per age band and per area
Donor matching (scoring rules):
  * a fresh urgent request is simulated for every blood type at every centre
  * selection rate among eligible, compatible donors is compared across age bands (age is NOT a scoring factor,
    so rates should be similar) and across areas (differences mostly reflect distance, which IS a factor)
  * "four-fifths rule": a group whose rate is below 80 % of the best group's rate is flagged for review
All data here is SIMULATED in this prototype — the checks show the method, not real-world performance.
"""
from __future__ import annotations

from datetime import date

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold

from . import matching
from .churn import features, nearest_centre_km
from .schemas import Centre, DonorHealth, MatchRequest, Profile, UrgentRequest
from .util import add_days

AGE_BANDS = [(17, 24, "17–24"), (25, 34, "25–34"), (35, 44, "35–44"), (45, 54, "45–54"), (55, 70, "55+")]
FOUR_FIFTHS = 0.8
MIN_GROUP = 15  # groups smaller than this are shown but not flagged (too noisy)


def age_band(birth_year: int, today: str) -> str:
    age = int(today[:4]) - birth_year
    return next((label for lo, hi, label in AGE_BANDS if lo <= age <= hi), "other")


def _dataset(profiles: list[Profile], health: list[DonorHealth], centres: list[Centre], today: str):
    km = {p.id: nearest_centre_km(p, centres) for p in profiles if p.role == "donor"}
    area = {p.id: p.area or "Unknown" for p in profiles}
    snapshot = add_days(today, -180)
    X, y, groups_age, groups_area = [], [], [], []
    for h in health:
        if h.donor_id not in km:
            continue
        x = features(h, km[h.donor_id], snapshot)
        if x is None:
            continue
        X.append(x)
        y.append(1 if any(snapshot < d <= today for d in h.donations) else 0)
        groups_age.append(age_band(h.birth_year, today))
        groups_area.append(area.get(h.donor_id, "Unknown"))
    return np.array(X), np.array(y), np.array(groups_age), np.array(groups_area)


def _group_table(groups: np.ndarray, y: np.ndarray, p: np.ndarray) -> list[dict]:
    out = []
    for g in sorted(set(groups)):
        m = groups == g
        n = int(m.sum())
        auc = float(roc_auc_score(y[m], p[m])) if n >= 10 and len(set(y[m])) > 1 else None
        out.append({"group": str(g), "n": n, "actual_rate": round(float(y[m].mean()), 3),
                    "predicted_rate": round(float(p[m].mean()), 3), "auc": None if auc is None else round(auc, 3),
                    "gap": round(float(p[m].mean() - y[m].mean()), 3)})
    return out


def evaluate_return_model(profiles: list[Profile], health: list[DonorHealth], centres: list[Centre], today: str) -> dict:
    X, y, ages, areas = _dataset(profiles, health, centres, today)
    if len(y) < 40 or len(set(y)) < 2:
        return {"available": False, "reason": "Not enough donors with history to evaluate."}
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=7)
    aucs, accs, briers = [], [], []
    oof = np.zeros(len(y))  # out-of-fold predictions: every donor scored by a model that never saw them
    for tr, te in folds.split(X, y):
        model = LogisticRegression(C=1.0, max_iter=1000).fit(X[tr], y[tr])
        p = model.predict_proba(X[te])[:, 1]
        oof[te] = p
        aucs.append(roc_auc_score(y[te], p))
        accs.append(accuracy_score(y[te], (p >= 0.5).astype(int)))
        briers.append(brier_score_loss(y[te], p))
    bins = np.clip((oof * 5).astype(int), 0, 4)
    calibration = [{"bin": f"{i * 20}–{(i + 1) * 20}%", "n": int((bins == i).sum()),
                    "predicted": round(float(oof[bins == i].mean()), 3) if (bins == i).any() else None,
                    "actual": round(float(y[bins == i].mean()), 3) if (bins == i).any() else None} for i in range(5)]
    by_age, by_area = _group_table(ages, y, oof), _group_table(areas, y, oof)
    flags = [f"{t['group']}: predicted {t['predicted_rate']:.0%} vs actual {t['actual_rate']:.0%}"
             for t in by_age + by_area if t["n"] >= MIN_GROUP and abs(t["gap"]) >= 0.1]
    return {
        "available": True, "n": int(len(y)), "folds": 5, "base_rate": round(float(y.mean()), 3),
        "auc": round(float(np.mean(aucs)), 3), "auc_sd": round(float(np.std(aucs)), 3),
        "accuracy": round(float(np.mean(accs)), 3), "brier": round(float(np.mean(briers)), 3),
        "brier_baseline": round(float(np.mean((y - y.mean()) ** 2)), 3),
        "calibration": calibration, "by_age": by_age, "by_area": by_area, "flags": flags,
    }


def evaluate_matching(profiles: list[Profile], health: list[DonorHealth], centres: list[Centre], today: str,
                      units: int = 4) -> dict:
    by_id = {p.id: p for p in profiles}
    births = {h.donor_id: h.birth_year for h in health}
    n_don = {h.donor_id: len(h.donations) for h in health}
    stats: dict[str, dict[str, list[float]]] = {"age": {}, "area": {}, "distance": {}}
    requests = 0
    for c in centres:
        for bt in matching.COMPATIBLE_DONORS:
            req = UrgentRequest(id=f"eval-{c.id}-{bt}", centre_id=c.id, blood_type=bt, units=units,
                                needed_by=add_days(today, 2), note="", status="open", created_at=today)
            res = matching.match_donors(MatchRequest(today=today, request=req, centre=c, profiles=profiles,
                                                     health=health, alerts=[]))
            requests += 1
            for cand in res.candidates:
                p = by_id.get(cand.donor_id)
                keys = {
                    "age": age_band(births.get(cand.donor_id, 1990), today),
                    "area": (p.area if p else "") or "Unknown",
                    "distance": "< 5 km" if cand.km < 5 else "5–15 km" if cand.km < 15 else "15 km +",
                }
                for dim, g in keys.items():
                    s = stats[dim].setdefault(g, [0, 0, 0.0, 0.0])
                    s[0] += 1
                    s[1] += int(cand.selected)
                    s[2] += cand.km
                    s[3] += n_don.get(cand.donor_id, 0)

    def table(dim: str) -> list[dict]:
        rows = [{"group": g, "eligible": int(n), "selected": int(k), "rate": round(k / n, 3) if n else 0.0,
                 "avg_km": round(km / n, 1) if n else None, "avg_donations": round(d / n, 1) if n else None}
                for g, (n, k, km, d) in sorted(stats[dim].items())]
        big = [r for r in rows if r["eligible"] >= MIN_GROUP]
        best = max((r["rate"] for r in big), default=0)
        for r in rows:
            r["ratio"] = round(r["rate"] / best, 2) if best else None
            r["flag"] = bool(r["eligible"] >= MIN_GROUP and best and r["rate"] / best < FOUR_FIFTHS)
        return rows

    age, area, dist = table("age"), table("area"), table("distance")
    return {
        "requests_simulated": requests, "units_per_request": units,
        "by_age": age, "by_area": area, "by_distance": dist,
        "age_flags": [r["group"] for r in age if r["flag"]],
        "area_flags": [r["group"] for r in area if r["flag"]],
        "explanation": _explain(age),
        "note": "Age is not a scoring factor, so age-band selection rates should be similar. Area differences "
                "mostly follow distance to the centre, which is an intended factor (shorter trips → more donors "
                "actually come). Flags use the four-fifths rule and need human review, not automatic changes.",
    }


def _explain(age_rows: list[dict]) -> str:
    flagged = [r for r in age_rows if r["flag"]]
    if not flagged:
        return "No age band falls below four-fifths of the best band's selection rate."
    best = max(age_rows, key=lambda r: r["rate"])
    parts = [f"{r['group']} (avg {r['avg_km']} km, {r['avg_donations']} past donations)" for r in flagged]
    return (f"Flagged: {', '.join(parts)} vs {best['group']} (avg {best['avg_km']} km, {best['avg_donations']} donations). "
            "Age is not used in the score, so the gap most likely comes from factors that differ between these "
            "groups — here distance and past donations (the 'regular donor' points). "
            "Options: cap the regular-donor points, or reserve a share of alerts for first-time donors — "
            "decide with the blood bank, then re-run this check.")


def evaluate_all(profiles, health, centres) -> dict:
    today = date.today().isoformat()
    return {"return_model": evaluate_return_model(profiles, health, centres, today),
            "matching": evaluate_matching(profiles, health, centres, today)}
