"""Tests for HemoCare (medical knowledge + medication history); run: python -m pytest -q"""
import os
import tempfile
from datetime import date, timedelta
from pathlib import Path

if "HEMOLINK_DB_PATH" not in os.environ:
    os.environ["HEMOLINK_DB_PATH"] = str(Path(tempfile.mkdtemp()) / "tests.db")

from fastapi.testclient import TestClient

from ai.hemocare import knowledge, meds
from app import app

H = {"X-HemoLink-Request": "app"}


def client(email="donor@demo.com", password="Demo123!"):
    c = TestClient(app)
    assert c.post("/api/login", json={"email": email, "password": password}, headers=H).status_code == 200
    return c


def d(days):
    return (date.today() + timedelta(days=days)).isoformat()


def test_medicine_detection_and_waiting_periods():
    assert meds.detect("Roaccutane 20mg") == "isotretinoin"
    assert meds.detect("Amoxicillin 500mg") == "antibiotic"
    assert meds.detect("Panadol") == "paracetamol"
    assert meds.detect("Mystery syrup") == "other"
    s = meds.status({"name": "Amoxicillin", "end_date": d(-2)})
    assert s["state"] == "hold" and s["until"] == d(12)  # PDN: 2 weeks after the last dose
    assert meds.status({"name": "Amoxicillin", "end_date": d(-30)})["state"] == "ok"
    assert meds.status({"name": "Accutane", "end_date": None})["state"] == "hold"
    assert meds.status({"name": "Amlodipine"})["state"] == "tell"
    h = meds.hold([{"name": "Accutane", "end_date": None}, {"name": "Panadol"}])
    assert h["ongoing"] and h["medicines"] == ["Accutane"]


def test_articles_and_hemoscan_links():
    assert len(knowledge.ARTICLES) >= 8
    a = knowledge.article("anaemia")
    assert a["sections"] and a["donation"] and a["urgent"] and a["refs"]
    ids = [x["id"] for x in knowledge.for_rules(["microcytic_anaemia", "mentzer"])]
    assert "iron" in ids and "thalassaemia" in ids
    for art in knowledge.ARTICLES:  # no dosing advice in the educational content
        text = " ".join(" ".join(p) for _, p in art["sections"]).lower()
        assert " mg daily" not in text and "take 1" not in text


def test_medicine_hold_defers_eligibility_and_matching():
    donor, admin = client(), client("admin@demo.com")
    r = donor.post("/api/hemocare/meds", json={"name": "Roaccutane 20mg", "reason": "Acne", "start_date": d(-30)}, headers=H)
    assert r.status_code == 200 and r.json()["status"]["state"] == "hold"
    mid = r.json()["id"]
    st = donor.get("/api/eligibility").json()["status"]
    assert st["verdict"] == "deferred" and any(c["label"].startswith("Medicines") for c in st["checks"])
    rid = admin.post("/api/requests", json={"blood_type": "O-", "units": 2, "needed_by": d(2)}, headers=H).json()["id"]
    cands = admin.get(f"/api/requests/{rid}").json()["match"]["candidates"]
    assert not any(c["name"].startswith("Amira") for c in cands)
    assert donor.post(f"/api/hemocare/meds/{mid}/stop", json={"end_date": d(0)}, headers=H).status_code == 200
    assert donor.get("/api/eligibility").json()["status"]["eligible_from"] >= d(30)
    assert donor.delete(f"/api/hemocare/meds/{mid}", headers=H).status_code == 200
    admin.post(f"/api/requests/{rid}/close", json={}, headers=H)


def test_medication_validation_and_privacy():
    donor = client()
    assert donor.post("/api/hemocare/meds", json={"name": "X"}, headers=H).status_code == 422
    assert donor.post("/api/hemocare/meds", json={"name": "Panadol", "category": "bogus"}, headers=H).status_code == 422
    assert donor.post("/api/hemocare/meds", json={"name": "Panadol", "start_date": d(-1), "end_date": d(-5)},
                      headers=H).status_code == 422
    mid = donor.post("/api/hemocare/meds", json={"name": "Ferrous fumarate", "reason": "Low iron"}, headers=H).json()["id"]
    other = TestClient(app)
    other.post("/api/signup", json={"agree_privacy": True, "name": "Other Donor", "email": "other.hemocare@example.com", "password": "Password1!",
                                    "blood_type": "A+", "city": "Kuala Lumpur"}, headers=H)
    assert not other.get("/api/hemocare/meds").json()["items"]
    assert other.delete(f"/api/hemocare/meds/{mid}", headers=H).status_code == 404
    assert client("organizer@demo.com").get("/api/hemocare/meds").status_code == 403
    assert client("admin@demo.com").get("/api/hemocare/overview").status_code == 403
    summary = donor.get("/api/hemocare/prep/summary").text
    assert "Ferrous fumarate" in summary and "Donation screening summary" in summary
    assert donor.get("/api/hemocare/articles/iron").json()["title"] == "Iron deficiency"
    assert donor.get("/api/hemocare/articles/nope").status_code == 404
    donor.delete(f"/api/hemocare/meds/{mid}", headers=H)
