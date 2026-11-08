"""
AI feature 4 — Donor return prediction (scikit-learn).

Training set: snapshot = 180 days ago. Features describe each donor at the snapshot; the label
is whether they donated again within the next 180 days. A logistic regression is trained on 75%
of donors and evaluated on the other 25% (AUC + accuracy), then scores every donor today.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split

from .schemas import Centre, DonorHealth, Profile, ReturnModelInfo, ReturnResponse, ReturnScore, TrainReport
from .util import add_days, days_between, haversine_km

FEATURE_NAMES = [
    "Years since last donation",
    "Donations in prior 2 years",
    "Past no-shows",
    "Distance to nearest centre (10 km)",
]


def nearest_centre_km(p: Profile, centres: list[Centre]) -> float:
    return min(haversine_km(p.lat, p.lng, c.lat, c.lng) for c in centres)


def features(h: DonorHealth, km_nearest: float, at: str) -> Optional[list[float]]:
    past = [d for d in h.donations if d <= at]
    if not past:
        return None
    two_years_ago = add_days(at, -730)
    return [
        days_between(past[-1], at) / 365,
        float(sum(1 for d in past if d > two_years_ago)),
        float(h.no_shows),
        km_nearest / 10,
    ]


def train_and_score(profiles: list[Profile], health: list[DonorHealth], centres: list[Centre], today: str) -> ReturnResponse:
    km = {p.id: nearest_centre_km(p, centres) for p in profiles if p.role == "donor"}
    snapshot = add_days(today, -180)

    X, y = [], []
    for h in health:
        if h.donor_id not in km:
            continue
        x = features(h, km[h.donor_id], snapshot)
        if x is None:
            continue
        X.append(x)
        y.append(1 if any(snapshot < d <= today for d in h.donations) else 0)
    X_arr, y_arr = np.array(X), np.array(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X_arr, y_arr, test_size=0.25, random_state=7, stratify=y_arr if len(set(y)) > 1 else None
    )
    model = LogisticRegression(C=1.0, max_iter=1000)
    model.fit(X_train, y_train)
    proba = model.predict_proba(X_test)[:, 1]
    auc = float(roc_auc_score(y_test, proba)) if len(set(y_test)) > 1 else 0.5
    acc = float(accuracy_score(y_test, (proba >= 0.5).astype(int)))

    weights = model.coef_[0]
    scores: list[ReturnScore] = []
    for h in health:
        if h.donor_id not in km:
            continue
        x = features(h, km[h.donor_id], today)
        if x is None:
            continue
        p = float(model.predict_proba(np.array([x]))[0, 1])
        contributions = np.array(x) * weights
        scores.append(ReturnScore(
            donor_id=h.donor_id,
            p_return=p,
            days_since_last=days_between(h.donations[-1], today),
            top_factor=FEATURE_NAMES[int(np.argmin(contributions))],
        ))

    report = TrainReport(
        model=ReturnModelInfo(weights=[float(w) for w in weights], bias=float(model.intercept_[0])),
        train_size=len(X_train),
        test_size=len(X_test),
        accuracy=acc,
        auc=auc,
        base_rate=float(y_arr.mean()) if len(y_arr) else 0.0,
        feature_names=FEATURE_NAMES,
    )
    return ReturnResponse(report=report, scores=scores)
