"""
Shortage outlook — turns donation forecasting into "which blood type runs out, and when".

For each blood type:
  * supply  = Random Forest forecast of units COLLECTED per day (same model as the trends page)
  * demand  = Random Forest forecast of units USED per day
  * stock   = today's inventory + forecast collected - forecast used, day by day for 7 days
  * status  = red / amber / green against the inventory's alert threshold (the safe level)

The blood bank's own daily history (`stock_history`) is SIMULATED in this prototype, because the
public MOH dataset only reports donations collected, not hospital usage or stock.
"""
from __future__ import annotations

import pandas as pd

from forecast import rf_fit_forecast

HORIZON = 7


def _series(history: list[dict], blood_type: str, column: str) -> pd.DataFrame:
    rows = [(h["date"], h[column]) for h in history if h["blood_type"] == blood_type]
    df = pd.DataFrame(rows, columns=["date", "donations"])
    df["date"] = pd.to_datetime(df["date"])
    return df.groupby("date", as_index=False)["donations"].sum().sort_values("date")


def fit_type(history: list[dict], blood_type: str) -> dict:
    """The slow part (two Random Forests). Cached by the caller until the history changes."""
    coll = _series(history, blood_type, "collected")
    used = _series(history, blood_type, "used")
    fc = rf_fit_forecast(coll, HORIZON)
    fu = rf_fit_forecast(used, HORIZON)
    last28_used = float(used["donations"].tail(28).mean()) if len(used) else 0.0
    last14 = float(coll["donations"].tail(14).mean()) if len(coll) else 0.0
    prior28 = float(coll["donations"].iloc[-42:-14].mean()) if len(coll) >= 42 else 0.0
    recent = [
        {"date": d.date().isoformat(), "collected": int(c), "used": int(u)}
        for d, c, u in zip(coll["date"].tail(14), coll["donations"].tail(14), used["donations"].tail(14))
    ]
    return {
        "collected": fc["future"],
        "used": fu["future"],
        "metrics": {"collected": fc["metrics"], "used": fu["metrics"]},
        "avg_daily_use": round(last28_used, 1),
        "supply_trend_pct": round((last14 - prior28) / prior28 * 100) if prior28 > 0 else 0,
        "recent": recent,
    }


def project(fit: dict, units: int, threshold: int) -> dict:
    """Cheap part: apply today's stock to the cached forecasts."""
    stock = float(units)
    points = []
    days_until_unsafe = 0 if units < threshold else None
    days_until_empty = 0 if units <= 0 else None
    for k, (c, u) in enumerate(zip(fit["collected"], fit["used"])):
        stock = max(0.0, stock + c["donations"] - u["donations"])
        points.append({"date": c["date"], "collected": c["donations"], "used": u["donations"], "stock": round(stock)})
        if days_until_unsafe is None and stock < threshold:
            days_until_unsafe = k + 1
        if days_until_empty is None and stock <= 0:
            days_until_empty = k + 1

    avg = fit["avg_daily_use"]
    days_of_supply = round(units / avg, 1) if avg > 0 else 99.0
    # very low-volume types swing a lot, so a projected dip only counts when supply is under a week
    status = "green"
    if units < threshold or (days_until_unsafe is not None and days_until_unsafe <= 3 and days_of_supply < 7):
        status = "red"
    elif days_of_supply < 5 or (days_until_unsafe is not None and days_of_supply < 10):
        status = "amber"
    return {
        "units": units,
        "threshold": threshold,
        "days_of_supply": days_of_supply,
        "days_until_unsafe": days_until_unsafe,
        "days_until_empty": days_until_empty,
        "status": status,
        "points": points,
    }


STATUS_ORDER = {"red": 0, "amber": 1, "green": 2}
