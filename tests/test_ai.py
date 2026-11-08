"""Tests for the v2 AI features; run: python -m pytest -q"""
import os
import tempfile
from datetime import date, timedelta
from pathlib import Path

if "HEMOLINK_DB_PATH" not in os.environ:
    os.environ["HEMOLINK_DB_PATH"] = str(Path(tempfile.mkdtemp()) / "tests.db")

from fastapi.testclient import TestClient

from app import app

H = {"X-HemoLink-Request": "app"}


def client(role):
    c = TestClient(app)
    r = c.post("/api/login", json={"email": f"{role}@demo.com", "password": "Demo123!"}, headers=H)
    assert r.status_code == 200, r.text
    return c


def soon(days=2):
    return (date.today() + timedelta(days=days)).isoformat()


# ---------------- shortage outlook ----------------


def test_outlook_flags_o_negative_and_uses_random_forest():
    c = client("organizer")
    out = c.get("/api/outlook").json()
    types = {t["blood_type"]: t for t in out["types"]}
    assert len(types) == 8
    assert types["O-"]["status"] in ("red", "amber")
    assert out["most_urgent"]["status"] != "green"
    assert len(types["O+"]["points"]) == 7
    m = types["O+"]["metrics"]["used"]
    assert m["test_samples"] > 10 and "baseline_mae" in m
    assert "SIMULATED" in out["note"]


# ---------------- urgent request loop ----------------


def test_full_urgent_request_loop():
    org, donor = client("admin"), client("donor")  # urgent requests belong to the blood bank admin (v3.1)
    before = {i["blood_type"]: i["units"] for i in org.get("/api/inventory").json()}

    r = org.post("/api/requests", json={"blood_type": "O-", "units": 3, "needed_by": soon(), "note": "test"}, headers=H)
    assert r.status_code == 200, r.text
    rid = r.json()["id"]

    detail = org.get(f"/api/requests/{rid}").json()
    cands = detail["match"]["candidates"]
    assert cands and all(c["blood_type"] == "O-" for c in cands)
    assert any(c["name"].startswith("Amira") for c in cands)
    assert cands == sorted(cands, key=lambda c: -c["score"])

    assert org.post(f"/api/requests/{rid}/alerts", json={}, headers=H).json()["sent"] >= 1

    alerts = donor.get("/api/my-alerts").json()
    mine = next(a for a in alerts if a["blood_type"] == "O-" and a["response"] is None)
    assert mine["reasons"]
    assert any("Urgent" in n["title"] for n in donor.get("/api/notifications").json())
    assert donor.post(f"/api/alerts/{mine['id']}/respond", json={"response": "yes"}, headers=H).status_code == 200

    org.post(f"/api/requests/{rid}/simulate", json={}, headers=H)
    detail = org.get(f"/api/requests/{rid}").json()
    yes_alert = next(a for a in detail["alerts"] if a["name"].startswith("Amira"))
    assert org.post(f"/api/alerts/{yes_alert['id']}/donated", json={}, headers=H).status_code == 200
    assert org.post(f"/api/alerts/{yes_alert['id']}/donated", json={}, headers=H).status_code == 409

    after = {i["blood_type"]: i["units"] for i in org.get("/api/inventory").json()}
    assert after["O-"] == before["O-"] + 1
    # the donor just donated, so the 90-day rule now defers her
    assert donor.get("/api/eligibility").json()["status"]["verdict"] == "deferred"


def test_request_permissions():
    donor = client("donor")
    assert donor.post("/api/requests", json={"blood_type": "O+", "units": 2, "needed_by": soon()}, headers=H).status_code == 403
    assert donor.get("/api/requests").status_code == 403
    assert client("organizer").post("/api/requests", json={"blood_type": "O+", "units": 2, "needed_by": soon()},
                                    headers=H).status_code == 403
    assert client("organizer").get("/api/requests").status_code == 403
    org = client("admin")
    assert org.post("/api/requests", json={"blood_type": "X+", "units": 2, "needed_by": soon()}, headers=H).status_code == 422
    assert org.post("/api/requests", json={"blood_type": "O+", "units": 2, "needed_by": soon(-3)}, headers=H).status_code == 422


# ---------------- eligibility ----------------


def test_eligibility_check_and_explanation(monkeypatch):
    for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    c = TestClient(app)
    c.post("/api/signup", json={"agree_privacy": True, "name": "Elig Tester", "email": "elig@example.com", "password": "longsecurepassword",
                                "blood_type": "B+", "city": "Shah Alam"}, headers=H)
    # profile incomplete -> clear message
    assert c.post("/api/eligibility/check", json={"answers": {}}, headers=H).status_code == 422
    assert c.patch("/api/me", json={"name": "Elig Tester", "blood_type": "B+", "city": "Shah Alam",
                                     "birth_year": 2000, "weight_kg": 60}, headers=H).status_code == 200
    ok = c.post("/api/eligibility/check", json={"answers": {"feelingWell": True}}, headers=H).json()
    assert ok["result"]["verdict"] == "eligible" and ok["used_llm"] is False and "Elig" in ok["explanation"]
    fever = c.post("/api/eligibility/check", json={"answers": {"fever": True}}, headers=H).json()
    assert fever["result"]["verdict"] == "deferred"
    assert c.post("/api/eligibility/check", json={"answers": {"chronic": True}}, headers=H).json()["result"]["verdict"] == "staff_check"


def test_profile_weight_validation():
    c = client("donor")
    bad = c.patch("/api/me", json={"name": "Amira Hassan", "blood_type": "O-", "city": "Cyberjaya", "weight_kg": 10}, headers=H)
    assert bad.status_code == 422


# ---------------- check-in, feedback, reports ----------------


def test_checkin_feedback_and_reports():
    org, donor = client("organizer"), client("donor")
    campaigns = donor.get("/api/campaigns").json()
    slot = campaigns[-1]["slots"][-1]["id"]
    booking = donor.post("/api/bookings", json={"slot_id": slot}, headers=H)
    assert booking.status_code == 200, booking.text
    bid = booking.json()["id"]
    assert donor.post("/api/feedback", json={"appointment_id": bid, "rating": 5}, headers=H).status_code == 409
    assert org.post(f"/api/organizer/bookings/{bid}/status", json={"status": "donated"}, headers=H).status_code == 200
    assert donor.post("/api/feedback", json={"appointment_id": bid, "rating": 5, "comment": "Great"}, headers=H).status_code == 200

    rep = org.get("/api/reports").json()
    assert rep["turnout"]["total"] > 0 and rep["ratings"]["count"] > 0
    assert rep["model"]["auc"] > 0.6 and len(rep["model"]["feature_names"]) == 4
    assert rep["suggestion"] is None or rep["suggestion"]["eligible_donors"] > 0
    assert client("donor").get("/api/reports").status_code == 403


def test_admin_models():
    m = client("admin").get("/api/models").json()
    assert len(m["forecast"]) == 8 and m["return_model"]["train_size"] > 50
    assert m["rules"]["wholeBloodIntervalDays"] == 90


# ---------------- assistant ----------------


def test_assistant_guardrail_and_faq(monkeypatch):
    for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    c = client("donor")
    med = c.post("/api/assistant", json={"question": "What dose of iron medicine should I take?"}, headers=H).json()
    assert med["source"] == "guardrail"
    faq = c.post("/api/assistant", json={"question": "How do I cancel my appointment?"}, headers=H).json()
    assert faq["source"] == "faq" and "My Appointments" in faq["answer"]
    elig = c.post("/api/assistant", json={"question": "Can I donate this week?"}, headers=H).json()
    assert "record" in elig["answer"]


def test_synthetic_donors_cannot_log_in():
    c = TestClient(app)
    r = c.post("/api/login", json={"email": "sim001@donors.hemolink.test", "password": "!synthetic-no-login"}, headers=H)
    assert r.status_code == 401


# ---------------- admin: users & organizers (v3.1) ----------------


def test_admin_approves_organizer():
    admin = client("admin")
    c = TestClient(app)
    c.post("/api/signup", json={"agree_privacy": True, "name": "Campus Club Lead", "email": "club.lead@example.com", "password": "longsecurepassword",
                                "blood_type": "A+", "city": "Kuala Lumpur"}, headers=H)
    uid = c.get("/api/me").json()["id"]
    assert c.post("/api/campaigns", json={"title": "Club Drive", "venue": "Main Hall", "city": "Kuala Lumpur",
                                          "event_date": soon(9), "times": ["09:00"], "capacity": 10}, headers=H).status_code == 403
    d = admin.get("/api/admin/users?q=club.lead").json()
    assert d["users"][0]["role"] == "donor" and d["counts"]["synthetic"] > 0
    assert all("donors.hemolink.test" not in u["email"] for u in admin.get("/api/admin/users").json()["users"])
    assert admin.patch(f"/api/admin/users/{uid}/role", json={"role": "organizer"}, headers=H).status_code == 200
    assert c.post("/api/campaigns", json={"title": "Club Drive", "venue": "Main Hall", "city": "Kuala Lumpur",
                                          "event_date": soon(9), "times": ["09:00"], "capacity": 10}, headers=H).status_code == 200
    assert any("Organizer access" in n["title"] for n in c.get("/api/notifications").json())
    admin_id = admin.get("/api/me").json()["id"]
    assert admin.patch(f"/api/admin/users/{admin_id}/role", json={"role": "donor"}, headers=H).status_code == 403
    assert client("organizer").get("/api/admin/users").status_code == 403


def test_pdn_rules_age_interval_and_new_questions():
    from ai import eligibility
    from ai.schemas import DonorHealth
    today = "2026-11-08"
    base = dict(donor_id="x", blood_type="O+", weight_kg=60)
    v = lambda **k: eligibility.evaluate(DonorHealth(**{**base, **k}), today)
    assert v(birth_year=2009).verdict == "staff_check"                       # 17: parent consent
    assert v(birth_year=2010).verdict == "not_eligible"                      # 16
    assert v(birth_year=1963).verdict == "not_eligible"                      # 63, first time (max 60)
    assert v(birth_year=1963, donations=["2025-01-01"]).verdict == "eligible"  # 63, regular donor
    assert v(birth_year=1958, donations=["2025-01-01"]).verdict == "staff_check"  # 68: yearly check-up
    assert v(birth_year=1954, donations=["2025-01-01"]).verdict == "not_eligible"  # 72
    # interval: women 120 days, men 90
    last = ["2026-07-20"]  # 111 days ago
    assert v(birth_year=1995, sex="male", donations=last).verdict == "eligible"
    w = v(birth_year=1995, sex="female", donations=last)
    assert w.verdict == "deferred" and w.eligible_from == "2026-11-17"
    q = {x["id"]: x for x in eligibility.RULES["questions"]}
    assert q["antibiotics"]["deferDays"] == 14 and q["dental"]["deferDays"] == 1 and q["dengue"]["deferDays"] == 180
    r = eligibility.evaluate(DonorHealth(**base, birth_year=1995), today, {"dengue": True})
    assert r.verdict == "deferred" and r.eligible_from == "2027-05-07"
    assert all(s["url"].startswith("https://") for s in eligibility.SOURCES)
