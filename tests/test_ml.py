"""Tests for model selection, cross-validation, evaluation and fairness; run: python -m pytest -q"""
import os
import tempfile
from pathlib import Path

if "HEMOLINK_DB_PATH" not in os.environ:
    os.environ["HEMOLINK_DB_PATH"] = str(Path(tempfile.mkdtemp()) / "tests.db")

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

import forecast as F
from app import app

H = {"X-HemoLink-Request": "app"}


def series(values, start="2025-01-01"):
    return pd.DataFrame({"date": pd.date_range(start, periods=len(values), freq="D"), "donations": values})


def test_simple_methods_follow_weekdays():
    weekly = [10, 20, 30, 40, 50, 60, 70] * 8
    s = series(weekly)
    assert F.predict("seasonal_naive", s, 7) == [float(v) for v in weekly[:7]]
    assert F.predict("weekday_mean", s, 7) == [float(v) for v in weekly[:7]]


def test_cross_validation_picks_simple_method_for_pure_weekly_pattern():
    s = series([10, 20, 30, 40, 50, 60, 70] * 30)
    fit = F.fit_forecast(s)
    m = fit["metrics"]
    assert m["selected"] in ("seasonal_naive", "weekday_mean")  # zero error → simplest wins ties
    assert m["mae"] == 0 and set(m["candidates"]) == set(F.METHODS)
    assert [p["donations"] for p in fit["future"]] == [10, 20, 30, 40, 50, 60, 70]


def test_random_forest_chosen_when_it_helps():
    rng = np.random.default_rng(1)
    n = 300
    trend = np.linspace(50, 150, n) + rng.normal(0, 2, n)  # strong trend: last-week copies lag behind
    fit = F.fit_forecast(series(np.round(trend)))
    assert fit["metrics"]["selected"] == "rf"
    assert fit["metrics"]["mae"] < fit["metrics"]["baseline_mae"]


def test_wide_moh_layout_is_read(monkeypatch, tmp_path):
    dates = pd.date_range("2025-01-01", periods=200, freq="D").strftime("%Y-%m-%d")
    rows = []
    for st in ("Malaysia", "Pulau Pinang"):
        for i, d in enumerate(dates):
            a, b, o, ab = 30 + i % 7, 32 + i % 5, 45 + i % 7, 8
            rows.append({"date": d, "state": st, "daily": a + b + o + ab, "blood_a": a, "blood_b": b, "blood_o": o, "blood_ab": ab})
    f = tmp_path / "donations_state.csv"
    pd.DataFrame(rows).to_csv(f, index=False)
    monkeypatch.setattr(F, "DATA_FILES", [f])
    F._forecast.cache_clear()
    assert F.regions() == ["Malaysia", "Pulau Pinang"]
    r = F.get_forecast("Penang", "O")  # alias → Pulau Pinang
    assert r["official"] and r["region"] == "Pulau Pinang" and len(r["future"]) == 7


def test_models_page_reports_evaluation_and_fairness():
    c = TestClient(app)
    c.post("/api/login", json={"email": "admin@demo.com", "password": "Demo123!"}, headers=H)
    m = c.get("/api/models").json()
    ev = m["evaluation"]
    assert ev["return_model"]["available"] and 0.5 < ev["return_model"]["auc"] <= 1
    assert len(ev["return_model"]["calibration"]) == 5
    assert ev["matching"]["requests_simulated"] > 0 and ev["matching"]["by_age"]
    assert all("selected" in f["used"] for f in m["forecast"])
