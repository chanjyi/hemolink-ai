"""
Personal data rights (PDPA 2010 — Access and Retention principles) and data retention.

  GET    /api/me/export     download everything HemoLink holds about you (JSON)
  DELETE /api/me            delete your donor account and all your data (password needed)
  GET    /api/me/consents   what you agreed to, and when
Retention (runs with the scheduled jobs):
  * original HemoScan report files are deleted after HEMOLINK_REPORT_FILE_DAYS (default 365); the confirmed values stay
  * the message delivery log keeps 90 days
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

import security
from app import COOKIE, connect, rows, user_from_request, verify_password

router = APIRouter()
DEMO_DOMAIN = "@demo.com"  # shared demo logins can't be deleted, so the public demo keeps working


@router.get("/api/me/export")
def export_my_data(request: Request, user=Depends(user_from_request)):
    security.limit(f"export:{user['id']}", 5, 3600, "You can download your data 5 times an hour.")
    uid = user["id"]
    with connect() as db:
        profile = dict(db.execute("""SELECT id,name,email,role,blood_type,city,birth_year,weight_kg,sex,phone,lang,
                                     notify_email,notify_sms,notify_push,notify_nearby,created_at FROM users WHERE id=?""",
                                  (uid,)).fetchone())
        q = lambda sql: rows(db.execute(sql, (uid,)))  # noqa: E731
        data = {
            "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "about": "Everything HemoLink AI stores about you. Uploaded report files are not included — open them in "
                     "HemoScan. Passwords are stored only as a one-way hash and are never exported.",
            "profile": profile,
            "consents": q("SELECT kind, version, created_at FROM consents WHERE user_id=? ORDER BY id"),
            "appointments": q("""SELECT a.id, c.title AS campaign, c.venue, c.event_date, s.start_time, a.status, a.created_at
                                 FROM appointments a JOIN slots s ON s.id=a.slot_id JOIN campaigns c ON c.id=s.campaign_id
                                 WHERE a.donor_id=? ORDER BY c.event_date"""),
            "donations": q("SELECT donated_on, source FROM donations WHERE donor_id=? ORDER BY donated_on"),
            "urgent_request_alerts": q("""SELECT sent_at, response, responded_at, donated FROM alerts WHERE donor_id=?
                                          ORDER BY sent_at"""),
            "feedback": q("""SELECT c.title AS campaign, f.rating, f.comment, f.created_at FROM feedback f
                             JOIN campaigns c ON c.id=f.campaign_id WHERE f.donor_id=?"""),
            "notifications": q("SELECT title, body, is_read, created_at FROM notifications WHERE user_id=? ORDER BY id"),
            "hemoscan_reports": [],
            "medicines": q("""SELECT name, category, reason, dose_note, start_date, end_date, notes FROM hemo_meds
                              WHERE user_id=? ORDER BY id"""),
            "messages_sent": q("SELECT created_at, event, channel, status FROM outbox WHERE user_id=? ORDER BY id"),
            "push_devices": q("SELECT user_agent, created_at FROM push_subs WHERE user_id=?") if _has_col(db, "push_subs", "created_at")
            else q("SELECT user_agent FROM push_subs WHERE user_id=?"),
        }
        for r in q("""SELECT id, source, report_date, lab_name, sex, status, created_at, confirmed_at FROM hemo_reports
                      WHERE user_id=? ORDER BY report_date"""):
            r["results"] = rows(db.execute("""SELECT biomarker, value, unit, ref_low, ref_high, flag FROM hemo_results
                                               WHERE report_id=? ORDER BY id""", (r["id"],)))
            data["hemoscan_reports"].append(r)
    body = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    return Response(body, media_type="application/json", headers={
        "Content-Disposition": f'attachment; filename="hemolink-my-data-{datetime.now():%Y%m%d}.json"',
        "Cache-Control": "private, no-store"})


def _has_col(db, table: str, col: str) -> bool:
    return col in {r[1] for r in db.execute(f"PRAGMA table_info({table})")}


@router.get("/api/me/consents")
def my_consents(user=Depends(user_from_request)):
    with connect() as db:
        return {"current_version": security.PRIVACY_VERSION,
                "items": rows(db.execute("SELECT kind, version, created_at FROM consents WHERE user_id=? ORDER BY id DESC",
                                         (user["id"],)))}


class DeleteBody(BaseModel):
    password: str = Field(min_length=1, max_length=128)
    confirm: str = Field(max_length=20)


def erase_user(db, uid: int) -> list[str]:
    """Delete a user's personal data. Returns stored report file names to remove from disk after commit."""
    files = [r[0] for r in db.execute("SELECT stored_name FROM hemo_reports WHERE user_id=? AND stored_name IS NOT NULL", (uid,))]
    db.execute("DELETE FROM hemo_results WHERE report_id IN (SELECT id FROM hemo_reports WHERE user_id=?)", (uid,))
    for table, col in [("hemo_reports", "user_id"), ("hemo_meds", "user_id"), ("appointments", "donor_id"),
                       ("donations", "donor_id"), ("alerts", "donor_id"), ("feedback", "donor_id"),
                       ("notifications", "user_id"), ("outbox", "user_id"), ("push_subs", "user_id"),
                       ("consents", "user_id")]:
        db.execute(f"DELETE FROM {table} WHERE {col}=?", (uid,))
    db.execute("DELETE FROM users WHERE id=?", (uid,))
    return files


@router.delete("/api/me")
def delete_my_account(body: DeleteBody, request: Request, response: Response, user=Depends(user_from_request)):
    security.limit(f"delete:{security.client_ip(request)}", 5, 600)
    if user["role"] != "donor":
        raise HTTPException(403, "Organizer and admin accounts are closed by a blood bank admin. Please contact them.")
    if body.confirm.strip().upper() != "DELETE":
        raise HTTPException(422, 'Type DELETE to confirm.')
    with connect() as db:
        row = db.execute("SELECT email, password_hash FROM users WHERE id=?", (user["id"],)).fetchone()
        if row["email"].endswith(DEMO_DOMAIN):
            raise HTTPException(403, "The shared demo accounts can't be deleted. Create your own account to try this.")
        if not verify_password(body.password, row["password_hash"]):
            raise HTTPException(401, "Password is incorrect")
        if db.execute("SELECT 1 FROM campaigns WHERE organizer_id=?", (user["id"],)).fetchone():
            raise HTTPException(409, "You still own donation campaigns from when you were an organizer — ask an admin.")
        files = erase_user(db, user["id"])
        db.commit()
    from hemoscan_routes import REPORT_DIR
    for f in files:
        (REPORT_DIR / f).unlink(missing_ok=True)
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


# ---------------------------------------------------------------- retention (called from the scheduled jobs)


def run_retention() -> dict:
    from hemoscan_routes import REPORT_DIR
    days = int(os.getenv("HEMOLINK_REPORT_FILE_DAYS", "365"))
    with connect() as db:
        old = rows(db.execute("""SELECT id, stored_name FROM hemo_reports WHERE stored_name IS NOT NULL
                                 AND created_at < datetime('now', ?)""", (f"-{days} days",)))
        for r in old:
            db.execute("UPDATE hemo_reports SET stored_name=NULL WHERE id=?", (r["id"],))
        purged = db.execute("DELETE FROM outbox WHERE created_at < datetime('now','-90 days')").rowcount
        db.commit()
    for r in old:
        (REPORT_DIR / r["stored_name"]).unlink(missing_ok=True)
    return {"report_files_removed": len(old), "log_entries_removed": purged}
