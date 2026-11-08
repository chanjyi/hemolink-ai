"""Forecast daily counts (collected donations, or units used) with honest model selection.

For every series three methods compete:
  * seasonal_naive — repeat the same weekday from last week (the classic baseline)
  * weekday_mean   — average of the last 4 same weekdays (steadier for small / rare-type counts)
  * rf             — Random Forest on calendar + lag features, forecasting 7 days recursively
They are compared with ROLLING-ORIGIN CROSS-VALIDATION: the series is cut at several past dates, each method
forecasts the next 7 days without seeing them, and the errors are averaged. The method with the lowest error
is used (if two are within 2 %, the simpler one wins). So a Random Forest is only used where it actually helps.

Data: the official MOH Malaysia blood donation dataset (KKMNOW / data-darah-public, CC BY 4.0) when present in
data/; otherwise reproducible synthetic data for demonstrating the UI. These are donation COUNTS — not patient
demand, hospital usage or live stock.
"""
from __future__ import annotations

import json
import math
from datetime import timedelta
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_FILES = [DATA_DIR / "donations_state.csv", DATA_DIR / "blood_donations_state.csv"]  # MOH wide / KKMNOW long
MODEL_DIR = ROOT / "models"
DEFAULT_REGIONS = ["Malaysia", "Selangor", "W.P. Kuala Lumpur", "Johor", "Pulau Pinang", "Perak", "Sabah", "Sarawak"]
REGION_ALIASES = {"penang": "Pulau Pinang", "kuala lumpur": "W.P. Kuala Lumpur"}
GROUPS = ["all", "A", "B", "AB", "O"]
WIDE_COLUMNS = {"daily": "all", "blood_a": "A", "blood_b": "B", "blood_ab": "AB", "blood_o": "O"}
HISTORY_DAYS = 3 * 365  # train on the latest three years (patterns change; keeps training fast)
HORIZON = 7

METHODS = {
    "seasonal_naive": "Same weekday last week (seasonal naive)",
    "weekday_mean": "Average of the last 4 same weekdays",
    "rf": "Random Forest (65 trees, lag + calendar features)",
}
SIMPLICITY = {"seasonal_naive": 0, "weekday_mean": 1, "rf": 2}
TIE = 0.02  # within 2 % of the best error → prefer the simpler method


# ---------------------------------------------------------------- data


def data_file() -> Path | None:
    return next((p for p in DATA_FILES if p.exists()), None)


@lru_cache(maxsize=2)
def _table(path: str, mtime: float) -> pd.DataFrame:
    """Load either MOH layout into long format: date, state, blood_type, donations."""
    df = pd.read_csv(path)
    if "daily" in df.columns:  # MOH data-darah-public: one column per blood group
        cols = [c for c in WIDE_COLUMNS if c in df.columns]
        df = df.melt(id_vars=["date", "state"], value_vars=cols, var_name="blood_type", value_name="donations")
        df["blood_type"] = df["blood_type"].map(WIDE_COLUMNS)
    else:  # KKMNOW catalogue: already long
        df = df[["date", "state", "blood_type", "donations"]].copy()
        df["blood_type"] = df["blood_type"].astype(str).str.upper().replace({"ALL": "all"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "donations"])
    df["state"] = df["state"].astype(str)
    return df


def table() -> pd.DataFrame | None:
    f = data_file()
    return _table(str(f), f.stat().st_mtime) if f else None


def regions() -> list[str]:
    t = table()
    if t is None:
        return DEFAULT_REGIONS
    states = sorted(s for s in t["state"].unique() if s != "Malaysia")
    return (["Malaysia"] if "Malaysia" in set(t["state"]) else []) + states


def canonical_region(region: str) -> str:
    r = REGION_ALIASES.get(region.strip().casefold(), region.strip())
    for known in regions():
        if known.casefold() == r.casefold():
            return known
    raise ValueError("Unsupported region or blood group")


def demo_series(region: str, blood_type: str) -> pd.DataFrame:
    # Reproducible fictional data, NOT official observations.
    region_index = DEFAULT_REGIONS.index(region) if region in DEFAULT_REGIONS else 0
    group_factor = {"all": 1.0, "A": 0.26, "B": 0.27, "AB": 0.08, "O": 0.39}[blood_type]
    n = 540
    last_day = pd.Timestamp.today().normalize() - pd.Timedelta(days=1)
    dates = pd.date_range(end=last_day, periods=n, freq="D")
    rng = np.random.default_rng(850 + region_index * 17 + GROUPS.index(blood_type))
    base = (170 - region_index * 12) * group_factor
    values = []
    for i, d in enumerate(dates):
        weekend = 1.22 if d.dayofweek >= 5 else 0.92
        seasonal = 1 + 0.09 * math.sin(2 * math.pi * i / 90)
        values.append(max(0, round(base * weekend * seasonal + rng.normal(0, max(3, base * 0.15)))))
    return pd.DataFrame({"date": dates, "donations": values})


def load_series(region: str, blood_type: str):
    t = table()
    if t is None:
        return demo_series(region, blood_type), "Synthetic demonstration data (official data not imported)", False
    subset = t[(t["state"] == region) & (t["blood_type"] == blood_type)]
    subset = subset.groupby("date", as_index=False)["donations"].sum().sort_values("date")
    if len(subset) < 120:
        raise ValueError(f"Insufficient official records for {region} / {blood_type}.")
    subset = subset[subset["date"] > subset["date"].max() - pd.Timedelta(days=HISTORY_DAYS)]
    full_days = pd.date_range(subset["date"].min(), subset["date"].max(), freq="D")
    # missing dates stay missing (never invented as zero); methods that need them skip that window
    subset = subset.set_index("date").reindex(full_days).rename_axis("date").reset_index()
    return subset, "Ministry of Health Malaysia — National Blood Centre donation data (KKMNOW, CC BY 4.0)", True


# ---------------------------------------------------------------- features + methods


def features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().sort_values("date")
    out["dow"] = out.date.dt.dayofweek
    out["month"] = out.date.dt.month
    out["day_of_year_sin"] = np.sin(2 * np.pi * out.date.dt.dayofyear / 365.25)
    out["day_of_year_cos"] = np.cos(2 * np.pi * out.date.dt.dayofyear / 365.25)
    for lag in [1, 7, 14]:
        out[f"lag{lag}"] = out.donations.shift(lag)
    for window in [7, 28]:
        out[f"rolling{window}"] = out.donations.shift(1).rolling(window).mean()
    return out.dropna().reset_index(drop=True)


COLS = ["dow", "month", "day_of_year_sin", "day_of_year_cos", "lag1", "lag7", "lag14", "rolling7", "rolling28"]


def train_rf(raw: pd.DataFrame, trees: int = 65) -> RandomForestRegressor:
    frame = features(raw)
    if len(frame) < 65:
        raise ValueError("Not enough complete daily observations for the Random Forest")
    model = RandomForestRegressor(n_estimators=trees, max_depth=9, min_samples_leaf=3, random_state=42, n_jobs=1)
    model.fit(frame[COLS], frame["donations"])
    return model


def rf_predict(model: RandomForestRegressor, raw: pd.DataFrame, horizon: int = HORIZON) -> list[float]:
    history = raw.sort_values("date").set_index("date")["donations"].to_dict()
    last = raw["date"].max()
    out = []
    for step in range(1, horizon + 1):
        ts = last + pd.Timedelta(days=step)
        lags = [history.get(ts - pd.Timedelta(days=k)) for k in range(1, 29)]
        if any(v is None or pd.isna(v) for v in lags):
            raise ValueError("Recent dates are missing; the Random Forest can't extrapolate safely.")
        row = pd.DataFrame([{
            "dow": ts.dayofweek, "month": ts.month,
            "day_of_year_sin": math.sin(2 * math.pi * ts.dayofyear / 365.25),
            "day_of_year_cos": math.cos(2 * math.pi * ts.dayofyear / 365.25),
            "lag1": lags[0], "lag7": lags[6], "lag14": lags[13],
            "rolling7": float(np.mean(lags[:7])), "rolling28": float(np.mean(lags)),
        }])[COLS]
        y = max(0.0, float(model.predict(row)[0]))
        history[ts] = y
        out.append(y)
    return out


def _simple(method: str, raw: pd.DataFrame, horizon: int) -> list[float]:
    s = raw.sort_values("date")["donations"].to_numpy(dtype=float)
    if len(s) < 28:
        raise ValueError("Need at least 4 weeks of history")
    out = []
    for h in range(1, horizon + 1):
        pos = (h - 1) % 7
        same = [s[-7 * k + pos] for k in range(1, 5)]
        if method == "seasonal_naive":
            if np.isnan(same[0]):
                raise ValueError("Missing value last week")
            out.append(float(same[0]))
        else:
            vals = [v for v in same if not np.isnan(v)]
            if len(vals) < 2:
                raise ValueError("Too many missing weeks")
            out.append(float(np.mean(vals)))
    return out


def predict(method: str, raw: pd.DataFrame, horizon: int = HORIZON, trees: int = 65) -> list[float]:
    if method == "rf":
        return rf_predict(train_rf(raw, trees), raw, horizon)
    return _simple(method, raw, horizon)


def cross_validate(raw: pd.DataFrame, horizon: int = HORIZON, folds: int = 4, step: int = 7, trees: int = 40) -> dict:
    """Rolling-origin CV: cut the series at `folds` past dates, forecast `horizon` days, average the errors."""
    raw = raw.sort_values("date").reset_index(drop=True)
    n = len(raw)
    errors: dict[str, dict[str, list]] = {m: {"mae": [], "rmse": []} for m in METHODS}
    for i in range(folds):
        origin = n - horizon - step * i
        if origin < 60:
            break
        train, actual = raw.iloc[:origin], raw.iloc[origin:origin + horizon]["donations"].to_numpy(dtype=float)
        if np.isnan(actual).any():
            continue
        for m in METHODS:
            try:
                p = np.array(predict(m, train, horizon, trees))
            except ValueError:
                continue
            errors[m]["mae"].append(float(np.mean(np.abs(actual - p))))
            errors[m]["rmse"].append(float(np.sqrt(np.mean((actual - p) ** 2))))
    return {m: {"mae": round(float(np.mean(e["mae"])), 2), "mae_sd": round(float(np.std(e["mae"])), 2),
                "rmse": round(float(np.mean(e["rmse"])), 2), "folds": len(e["mae"])}
            for m, e in errors.items() if e["mae"]}


def choose(cv: dict) -> str:
    best = min(v["mae"] for v in cv.values())
    close = [m for m, v in cv.items() if v["mae"] <= best * (1 + TIE) + 1e-9]
    return min(close, key=lambda m: SIMPLICITY[m])


def fit_forecast(raw: pd.DataFrame, horizon: int = HORIZON, folds: int = 4, trees: int = 40) -> dict:
    """Cross-validate all methods, pick the best, forecast `horizon` days with it."""
    raw = raw.sort_values("date").reset_index(drop=True)
    cv = cross_validate(raw, horizon, folds=folds, trees=trees)
    if not cv:
        raise ValueError("Not enough complete history to evaluate a forecast")
    order = sorted(cv, key=lambda m: (m != choose(cv), cv[m]["mae"]))
    for method in order:  # fall back if the chosen method can't forecast from the latest data
        try:
            values = predict(method, raw, horizon, 65)
            break
        except ValueError:
            continue
    else:
        raise ValueError("Latest source has missing dates; cannot safely forecast.")
    last = raw["date"].max()
    base = cv.get("seasonal_naive", cv[method])
    folds_used = cv[method]["folds"]
    return {
        "metrics": {
            "mae": cv[method]["mae"], "mae_sd": cv[method]["mae_sd"], "rmse": cv[method]["rmse"],
            "baseline_mae": base["mae"], "test_samples": folds_used * horizon,
            "selected": method, "selected_label": METHODS[method],
            "candidates": {m: cv[m]["mae"] for m in cv},
            "validation": f"Rolling-origin cross-validation · {folds_used} cut-off dates × {horizon}-day forecasts",
        },
        "future": [{"date": (last + pd.Timedelta(days=k + 1)).date().isoformat(), "donations": max(0, round(v))}
                   for k, v in enumerate(values)],
        "last": last.date(),
    }


rf_fit_forecast = fit_forecast  # backwards-compatible name used by the stock outlook


# ---------------------------------------------------------------- trends page


def _saved(region: str, blood_type: str, f: Path | None) -> dict | None:
    """Results precomputed by scripts/train_models.py, used when they match the current data file."""
    p = MODEL_DIR / "forecast" / f"{region}__{blood_type}.json".replace(" ", "_").replace("/", "-")
    if not f or not p.exists():
        return None
    try:
        saved = json.loads(p.read_text())
    except (OSError, ValueError):
        return None
    st = f.stat()
    return saved if saved.get("data_size") == st.st_size and saved.get("data_name") == f.name else None


@lru_cache(maxsize=80)
def _forecast(region: str, blood_type: str, mtime: float):
    raw, source, official = load_series(region, blood_type)
    fit = fit_forecast(raw, folds=8 if official else 4)  # real data: more cut-off dates for a steadier choice
    hist = raw.dropna(subset=["donations"]).tail(28)
    return {
        "region": region, "blood_type": blood_type,
        "source": source, "official": official,
        "source_last_date": fit["last"].isoformat(),
        "history": [{"date": d.date().isoformat(), "donations": int(v)} for d, v in zip(hist.date, hist.donations)],
        "future": fit["future"],
        "metrics": fit["metrics"],
        "model": fit["metrics"]["selected_label"] + " — chosen by cross-validation",
        "trained": "on request",
        "warning": "This predicts historical-pattern donation counts, not patient needs, medical risk, or hospital "
                   "inventory. Not for clinical use.",
    }


def get_forecast(region: str, blood_type: str):
    if blood_type not in GROUPS:
        raise ValueError("Unsupported region or blood group")
    region = canonical_region(region)
    f = data_file()
    saved = _saved(region, blood_type, f)
    if saved:
        return saved["result"]
    return _forecast(region, blood_type, f.stat().st_mtime if f else 0.0)


REGIONS = DEFAULT_REGIONS  # kept for older imports; use regions() for the live list
