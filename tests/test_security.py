"""Security + personal data (PDPA) tests: rate limits, login lock, headers, encryption at rest, export, delete."""
import json
import os
import tempfile
from pathlib import Path

if "HEMOLINK_DB_PATH" not in os.environ:
    os.environ["HEMOLINK_DB_PATH"] = str(Path(tempfile.mkdtemp()) / "tests.db")

import pytest
from fastapi.testclient import TestClient

import security
from app import app, connect

H = {"X-HemoLink-Request": "app"}


@pytest.fixture
def limits_on(monkeypatch):
    monkeypatch.setenv("HEMOLINK_RATE_LIMIT", "on")
    security.reset_limits()
    yield
    security.reset_limits()


def signup(c, email, password="Correct-horse-1"):
    r = c.post("/api/signup", json={"name": "Privacy Tester", "email": email, "password": password,
                                    "agree_privacy": True, "blood_type": "O+"}, headers=H)
    assert r.status_code == 200, r.text


def test_signup_needs_privacy_consent_and_records_it():
    c = TestClient(app)
    r = c.post("/api/signup", json={"name": "No Consent", "email": "noconsent@example.com", "password": "Password123"},
               headers=H)
    assert r.status_code == 422 and "privacy" in r.json()["detail"].lower()
    signup(c, "consent@example.com")
    items = c.get("/api/me/consents").json()["items"]
    assert items and items[0]["kind"] == "privacy_notice" and items[0]["version"] == security.PRIVACY_VERSION


def test_login_lock_after_five_wrong_passwords(limits_on):
    c = TestClient(app)
    signup(c, "lockme@example.com")
    bad = {"email": "lockme@example.com", "password": "wrong-password"}
    assert [c.post("/api/login", json=bad, headers=H).status_code for _ in range(5)] == [401] * 5
    r = c.post("/api/login", json={**bad, "password": "Correct-horse-1"}, headers=H)
    assert r.status_code == 429 and "locked" in r.json()["detail"] and r.headers.get("retry-after")
    security.reset_limits()
    assert c.post("/api/login", json={**bad, "password": "Correct-horse-1"}, headers=H).status_code == 200


def test_assistant_rate_limit(limits_on):
    c = TestClient(app)
    c.post("/api/login", json={"email": "donor@demo.com", "password": "Demo123!"}, headers=H)
    codes = [c.post("/api/assistant", json={"question": "How do I book?"}, headers=H).status_code for _ in range(21)]
    assert codes[:20] == [200] * 20 and codes[20] == 429


def test_security_headers():
    r = TestClient(app).get("/")
    csp = r.headers["content-security-policy"]
    assert "script-src 'self'" in csp and "frame-ancestors 'none'" in csp and "object-src 'none'" in csp
    assert r.headers["x-frame-options"] == "DENY" and "geolocation=(self)" in r.headers["permissions-policy"]


def test_hemoscan_files_are_encrypted_at_rest():
    from ai.hemoscan import samples
    from hemoscan_routes import REPORT_DIR
    c = TestClient(app)
    signup(c, "encrypt@example.com")
    pdf = samples.make("latest")
    r = c.post("/api/hemoscan/reports/upload", files={"file": ("fbc.pdf", pdf, "application/pdf")},
               data={"consent": "true"}, headers=H)
    assert r.status_code == 200, r.text
    rid = r.json()["id"]
    with connect() as db:
        stored = db.execute("SELECT stored_name FROM hemo_reports WHERE id=?", (rid,)).fetchone()[0]
        kinds = [x[0] for x in db.execute("SELECT kind FROM consents c JOIN users u ON u.id=c.user_id "
                                          "WHERE u.email='encrypt@example.com'")]
    raw = (REPORT_DIR / stored).read_bytes()
    assert raw.startswith(security.ENC_MAGIC) and b"%PDF" not in raw  # unreadable on disk
    served = c.get(f"/api/hemoscan/reports/{rid}/file")
    assert served.status_code == 200 and served.content == pdf          # owner still sees the original
    assert c.get(f"/api/hemoscan/reports/{rid}/page/0").headers["content-type"] == "image/png"
    assert "hemoscan_upload" in kinds


def test_export_and_delete_my_account():
    from ai.hemoscan import samples
    from hemoscan_routes import REPORT_DIR
    c = TestClient(app)
    signup(c, "leaving@example.com", "Leaving-pass-9")
    rid = c.post("/api/hemoscan/reports/upload", files={"file": ("fbc.pdf", samples.make("latest"), "application/pdf")},
                 data={"consent": "true"}, headers=H).json()["id"]
    c.post("/api/hemocare/meds", json={"name": "Amoxicillin"}, headers=H)
    data = json.loads(c.get("/api/me/export").content)
    assert data["profile"]["email"] == "leaving@example.com" and "password_hash" not in json.dumps(data)
    assert data["hemoscan_reports"] and data["medicines"] and data["consents"]
    with connect() as db:
        stored = db.execute("SELECT stored_name FROM hemo_reports WHERE id=?", (rid,)).fetchone()[0]
    assert c.request("DELETE", "/api/me", json={"password": "wrong", "confirm": "DELETE"}, headers=H).status_code == 401
    assert c.request("DELETE", "/api/me", json={"password": "Leaving-pass-9", "confirm": "no"}, headers=H).status_code == 422
    assert c.request("DELETE", "/api/me", json={"password": "Leaving-pass-9", "confirm": "DELETE"}, headers=H).status_code == 200
    with connect() as db:
        assert db.execute("SELECT 1 FROM users WHERE email='leaving@example.com'").fetchone() is None
        assert db.execute("SELECT 1 FROM hemo_reports WHERE id=?", (rid,)).fetchone() is None
    assert not (REPORT_DIR / stored).exists()
    assert c.get("/api/me").status_code == 401


def test_demo_and_staff_accounts_cannot_self_delete():
    d = TestClient(app)
    d.post("/api/login", json={"email": "donor@demo.com", "password": "Demo123!"}, headers=H)
    assert d.request("DELETE", "/api/me", json={"password": "Demo123!", "confirm": "DELETE"}, headers=H).status_code == 403
    a = TestClient(app)
    a.post("/api/login", json={"email": "admin@demo.com", "password": "Demo123!"}, headers=H)
    assert a.request("DELETE", "/api/me", json={"password": "Demo123!", "confirm": "DELETE"}, headers=H).status_code == 403


def test_retention_removes_old_report_files(monkeypatch):
    from privacy_routes import run_retention
    monkeypatch.setenv("HEMOLINK_REPORT_FILE_DAYS", "0")
    with connect() as db:
        db.execute("UPDATE hemo_reports SET created_at=datetime('now','-1 day') WHERE stored_name IS NOT NULL")
        db.commit()
    out = run_retention()
    assert out["report_files_removed"] >= 1
    with connect() as db:
        assert db.execute("SELECT COUNT(*) FROM hemo_reports WHERE stored_name IS NOT NULL").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM hemo_results").fetchone()[0] > 0  # confirmed values are kept
