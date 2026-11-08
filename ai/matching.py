"""
AI feature 2 — Smart donor matching.

1. Filter: red-cell compatible + basic eligibility (age, weight, 90-day interval) + not already
   alerted for this request + within the radius.
2. Score 0–100 from distance, past response rate (smoothed), exact type match, "ready" donor,
   regular donor, and penalties for alert fatigue and past no-shows.
3. Estimate each donor's chance of saying yes and alert just enough donors to cover the units
   needed with a safety margin — not everyone.
"""
from __future__ import annotations

from .eligibility import is_basically_eligible
from .schemas import Alert, DonorHealth, Excluded, MatchCandidate, MatchRequest, MatchResult, Profile
from .util import clamp, days_between, haversine_km, js_round

# recipient -> donor types that can give red cells to them
COMPATIBLE_DONORS: dict[str, list[str]] = {
    "O-": ["O-"],
    "O+": ["O+", "O-"],
    "A-": ["A-", "O-"],
    "A+": ["A+", "A-", "O+", "O-"],
    "B-": ["B-", "O-"],
    "B+": ["B+", "B-", "O+", "O-"],
    "AB-": ["AB-", "A-", "B-", "O-"],
    "AB+": ["AB+", "AB-", "A+", "A-", "B+", "B-", "O+", "O-"],
}

WEIGHTS = {
    "distance": 30,
    "responseRate": 30,
    "exactType": 15,
    "ready": 10,
    "regular": 15,
    "fatiguePenalty": 15,
    "maxKm": 35,
}


def response_stats(alerts: list[Alert], donor_id: str) -> dict:
    mine = [a for a in alerts if a.donor_id == donor_id]
    yes = sum(1 for a in mine if a.response == "yes")
    # Bayesian smoothing: every donor starts at 1 yes out of 3 (~33%)
    rate = (yes + 1) / (len(mine) + 3)
    last_alert = max((a.sent_at[:10] for a in mine), default=None)
    return {"rate": rate, "count": len(mine), "yes": yes, "last_alert": last_alert}


def score_donor(today: str, alerts: list[Alert], health: DonorHealth, km: float, needed: str) -> MatchCandidate:
    stats = response_stats(alerts, health.donor_id)
    w = WEIGHTS
    dist_score = w["distance"] * clamp(1 - km / w["maxKm"], 0, 1)
    rate_score = w["responseRate"] * stats["rate"]
    exact = health.blood_type == needed
    exact_score = w["exactType"] if exact else w["exactType"] / 3
    last = health.donations[-1] if health.donations else None
    days_since = days_between(last, today) if last else None
    if days_since is None:
        ready_score = w["ready"] * 0.5
    else:
        ready_score = w["ready"] if days_since >= 120 else w["ready"] * 0.6
    n = len(health.donations)
    regular = n >= 3
    regular_score = w["regular"] if regular else (n / 3) * w["regular"]
    fatigued = stats["last_alert"] is not None and days_between(stats["last_alert"], today) < 7
    no_show_penalty = min(10, health.no_shows * 4)

    score = clamp(
        dist_score + rate_score + exact_score + ready_score + regular_score
        - (w["fatiguePenalty"] if fatigued else 0) - no_show_penalty,
        0, 100,
    )
    # chance of "yes": past response rate, discounted by distance
    p_yes = clamp(stats["rate"] * clamp(1.1 - km / 50, 0.2, 1), 0.02, 0.95)

    reasons = [f"{km:.1f} km away"]
    reasons.append(f"said yes to {stats['yes']} of {stats['count']} past alerts" if stats["count"] else "no alert history yet")
    reasons.append(f"exact match ({health.blood_type})" if exact else f"{health.blood_type} is compatible")
    if regular:
        reasons.append(f"regular donor ({n} donations)")
    if fatigued:
        reasons.append("alerted in the last 7 days")
    if health.no_shows > 0:
        reasons.append(f"{health.no_shows} past no-show{'s' if health.no_shows > 1 else ''}")

    return MatchCandidate(
        donor_id=health.donor_id,
        km=km,
        score=js_round(score),
        p_yes=js_round(p_yes * 100) / 100,
        response_rate=js_round(stats["rate"] * 100),
        alerts_received=stats["count"],
        reasons=reasons,
        selected=False,
    )


def match_donors(req: MatchRequest) -> MatchResult:
    request, centre = req.request, req.centre
    compatible = COMPATIBLE_DONORS[request.blood_type]
    excluded = Excluded()
    already = {a.donor_id for a in req.alerts if a.request_id == request.id}
    health_by_id = {h.donor_id: h for h in req.health}

    candidates: list[MatchCandidate] = []
    donor: Profile
    for donor in req.profiles:
        if donor.role != "donor":
            continue
        h = health_by_id.get(donor.id)
        if h is None:
            continue
        if h.blood_type not in compatible:
            excluded.not_compatible += 1
            continue
        if donor.id in already:
            excluded.already_alerted += 1
            continue
        if not is_basically_eligible(h, req.today):
            excluded.not_eligible += 1
            continue
        km = haversine_km(donor.lat, donor.lng, centre.lat, centre.lng)
        if km > WEIGHTS["maxKm"]:
            excluded.too_far += 1
            continue
        candidates.append(score_donor(req.today, req.alerts, h, km, request.blood_type))

    candidates.sort(key=lambda c: -c.score)  # stable sort, same order as the website

    expected_yes = 0.0
    selected = 0
    for c in candidates:
        if expected_yes >= request.units * req.margin or selected >= req.max_alerts:
            break
        c.selected = True
        expected_yes += c.p_yes
        selected += 1

    return MatchResult(
        candidates=candidates,
        selected_count=selected,
        expected_yes=js_round(expected_yes * 10) / 10,
        excluded=excluded,
    )
