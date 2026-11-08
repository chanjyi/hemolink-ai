"""Alerts, Bahasa Malaysia, map pin and AI-language tests; run: python -m pytest -q"""
import os
import tempfile
from datetime import date, timedelta
from pathlib import Path

if "HEMOLINK_DB_PATH" not in os.environ:
    os.environ["HEMOLINK_DB_PATH"] = str(Path(tempfile.mkdtemp()) / "tests.db")
os.environ.setdefault("HEMOLINK_SCHEDULER", "off")
for k in ("SMTP_HOST", "TWILIO_ACCOUNT_SID", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"):
    os.environ.pop(k, None)  # every outside channel runs in demo mode here

from fastapi.testclient import TestClient

import notifier
from ai import llm
from app import app, connect

H = {"X-HemoLink-Request": "app"}


def login(role):
    c = TestClient(app)
    r = c.post("/api/login", json={"email": f"{role}@demo.com", "password": "Demo123!"}, headers=H)
    assert r.status_code == 200, r.text
    return c


def outbox(event):
    notifier.wait_idle()
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT * FROM outbox WHERE event=? ORDER BY id", (event,))]


def test_settings_validate_phone_and_sms():
    c = login("donor")
    s = c.get("/api/notify/settings").json()
    assert {"lang", "phone", "notify_email", "notify_sms", "notify_push", "channels", "vapid_public_key"} <= set(s)
    assert "key" not in str(s["channels"]).lower() or "TWILIO_AUTH_TOKEN" not in str(s)
    bad = {"lang": "en", "phone": "abc", "notify_sms": True}
    assert c.put("/api/notify/settings", json=bad, headers=H).status_code == 422
    assert c.put("/api/notify/settings", json={"notify_sms": True, "phone": ""}, headers=H).status_code == 422
    ok = {"lang": "en", "phone": "012-345 6789", "notify_email": True, "notify_sms": True, "notify_push": True}
    assert c.put("/api/notify/settings", json=ok, headers=H).status_code == 200
    assert c.get("/api/notify/settings").json()["notify_sms"] is True
    assert notifier.normalise_phone("012-345 6789") == "+60123456789"


def test_booking_alerts_donor_and_organizer_in_malay():
    d = login("donor")
    assert d.patch("/api/me/lang", json={"lang": "ms"}, headers=H).status_code == 200
    d.put("/api/notify/settings", json={"lang": "ms", "phone": "0123456789", "notify_email": True, "notify_sms": True,
                                         "notify_push": True}, headers=H)
    camp = next(x for x in d.get("/api/campaigns").json() if x["slots"] and x["event_date"] >= date.today().isoformat())
    slot = next(s for s in camp["slots"] if s["booked"] < s["capacity"])
    r = d.post("/api/bookings", json={"slot_id": slot["id"]}, headers=H)
    assert r.status_code in (200, 409), r.text
    if r.status_code == 409:  # already booked by another test: cancel and rebook
        mine = next(b for b in d.get("/api/bookings").json() if b["status"] == "confirmed")
        d.post(f"/api/bookings/{mine['id']}/cancel", headers=H)
        assert d.post("/api/bookings", json={"slot_id": mine["slot_id"] if "slot_id" in mine else slot["id"]},
                      headers=H).status_code == 200
    titles = [n["title"] for n in d.get("/api/notifications").json()]
    assert "Temujanji disahkan" in titles, titles  # Malay template used
    sent = outbox("booking_confirmed")
    assert {o["channel"] for o in sent} == {"email"}  # SMS is kept for urgent requests and reminders
    assert all(o["status"] == "simulated" for o in sent)  # no SMTP / Twilio configured
    assert all("@" not in (o["to_addr"] or "") or "*" in o["to_addr"] for o in sent)  # recipients are masked
    o = login("organizer")
    assert any(camp["title"] in n["body"] for n in o.get("/api/notifications").json())
    d.patch("/api/me/lang", json={"lang": "en"}, headers=H)


def test_reminder_job_runs_once():
    with connect() as db:
        donor = db.execute("SELECT id FROM users WHERE email='donor@demo.com'").fetchone()["id"]
        org = db.execute("SELECT id FROM users WHERE email='organizer@demo.com'").fetchone()["id"]
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        cid = db.execute("""INSERT INTO campaigns(title,venue,city,event_date,description,organizer_id,lat,lng)
                            VALUES('Reminder test drive','Test Hall','Cyberjaya',?, '', ?, 2.92, 101.65)""",
                         (tomorrow, org)).lastrowid
        sid = db.execute("INSERT INTO slots(campaign_id,start_time,capacity) VALUES(?,?,5)", (cid, "10:00")).lastrowid
        db.execute("INSERT INTO appointments(donor_id,slot_id) VALUES(?,?)", (donor, sid))
        db.commit()
    a = login("admin")
    assert login("donor").post("/api/admin/jobs/run", headers=H).status_code == 403
    first = a.post("/api/admin/jobs/run", headers=H).json()
    assert first["reminders"] >= 1
    assert "sms" in {o["channel"] for o in outbox("reminder")}  # donor turned SMS on in the earlier test
    assert a.post("/api/admin/jobs/run", headers=H).json()["reminders"] == 0  # never twice
    log = a.get("/api/admin/outbox").json()
    assert log["items"] and "counts_7d" in log and "scheduler" in log


def test_campaign_pin_and_location_edit():
    o = login("organizer")
    when = (date.today() + timedelta(days=10)).isoformat()
    body = {"title": "Pinned test drive", "venue": "Dewan Komuniti", "city": "Shah Alam", "event_date": when,
            "times": ["09:00", "10:00"], "capacity": 5, "lat": 3.0733, "lng": 101.5185}
    r = o.post("/api/campaigns", json=body, headers=H)
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    assert "nearby_notified" in r.json()
    camp = next(c for c in o.get("/api/organizer/campaigns").json() if c["id"] == cid)
    assert abs(camp["lat"] - 3.0733) < 1e-6 and abs(camp["lng"] - 101.5185) < 1e-6
    assert o.patch(f"/api/campaigns/{cid}/location", json={"lat": 3.1, "lng": 101.6}, headers=H).status_code == 200
    assert o.patch(f"/api/campaigns/{cid}/location", json={"lat": 40, "lng": 101.6}, headers=H).status_code == 422
    assert login("donor").patch(f"/api/campaigns/{cid}/location", json={"lat": 3.1, "lng": 101.6},
                                headers=H).status_code == 403
    bad = {**body, "lat": 51.5, "lng": -0.12}  # outside Malaysia
    assert o.post("/api/campaigns", json=bad, headers=H).status_code == 422


def test_push_subscription_needs_https():
    d = login("donor")
    keys = {"p256dh": "B" * 87, "auth": "a" * 22}
    assert d.post("/api/push/subscribe", json={"endpoint": "http://example.com/push/x" * 2, "keys": keys},
                  headers=H).status_code == 422
    ep = "https://fcm.googleapis.com/fcm/send/test-device-123"
    assert d.post("/api/push/subscribe", json={"endpoint": ep, "keys": keys}, headers=H).status_code == 200
    assert d.get("/api/notify/settings").json()["push_devices"] >= 1
    assert d.request("DELETE", "/api/push/subscribe", json={"endpoint": ep}, headers=H).status_code == 200


def test_ai_answers_follow_app_language(monkeypatch):
    seen = {}

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"content": [{"text": "Jawapan ujian"}]}

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, headers=None, json=None, **k):
            seen["system"] = json["system"]
            return FakeResp()

    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(llm.httpx, "Client", FakeClient)
    d = login("donor")
    r = d.post("/api/assistant", json={"question": "How do I book an appointment?"}, headers={**H, "X-HemoLink-Lang": "ms"})
    assert r.status_code == 200 and r.json()["source"] == "llm"
    assert "Bahasa Melayu" in seen["system"]
    d.post("/api/assistant", json={"question": "How do I book an appointment?"}, headers=H)
    assert "Bahasa Melayu" not in seen["system"]
    assert "test-key" not in str(d.get("/api/admin/models").json() if False else llm.status())
