"""
Alert settings, web-push devices, delivery log and scheduled jobs.

  GET/PUT /api/notify/settings      language, phone, email / SMS / push / nearby-drive switches
  POST    /api/push/subscribe       save this browser's push subscription      DELETE same → remove it
  POST    /api/notify/test          send yourself a test on every channel
  GET     /api/admin/outbox         channel status + last 80 delivery attempts (admin)
  POST    /api/admin/jobs/run       run reminders / "eligible again" now (admin)
  GET     /sw.js                    service worker that shows push notifications
Scheduled jobs (every 15 min while the app is running; set HEMOLINK_SCHEDULER=off to disable):
  * reminder the day before each confirmed appointment
  * "you can donate again" on the day a real donor becomes eligible after their last donation
"""
from __future__ import annotations

import asyncio
import os
from datetime import date, timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import notifier
import security
from ai import eligibility
from app import ROOT, connect, only, rows, user_from_request

router = APIRouter()


class SettingsBody(BaseModel):
    lang: Literal["en", "ms"] = "en"
    phone: str = Field(default="", max_length=24)
    notify_email: bool = True
    notify_sms: bool = False
    notify_push: bool = True
    notify_nearby: bool = True


@router.get("/api/notify/settings")
def get_settings(user=Depends(user_from_request)):
    with connect() as db:
        u = db.execute("""SELECT lang, phone, notify_email, notify_sms, notify_push, notify_nearby FROM users WHERE id=?""",
                       (user["id"],)).fetchone()
        devices = db.execute("SELECT COUNT(*) FROM push_subs WHERE user_id=?", (user["id"],)).fetchone()[0]
    return {**{k: (bool(u[k]) if k.startswith("notify_") else u[k]) for k in u.keys()}, "phone": u["phone"] or "",
            "push_devices": devices, "vapid_public_key": notifier.vapid_public_key(), "channels": notifier.status()}


@router.put("/api/notify/settings")
def put_settings(body: SettingsBody, user=Depends(user_from_request)):
    phone = body.phone.strip()
    if phone and not notifier.normalise_phone(phone):
        raise HTTPException(422, "Please enter a valid phone number, e.g. 012-345 6789.")
    if body.notify_sms and not phone:
        raise HTTPException(422, "Add your phone number to turn on SMS alerts.")
    with connect() as db:
        db.execute("""UPDATE users SET lang=?, phone=?, notify_email=?, notify_sms=?, notify_push=?, notify_nearby=?
                      WHERE id=?""", (body.lang, phone, int(body.notify_email), int(body.notify_sms),
                                      int(body.notify_push), int(body.notify_nearby), user["id"]))
        db.commit()
    return {"ok": True}


class SubKeys(BaseModel):
    p256dh: str = Field(min_length=20, max_length=200)
    auth: str = Field(min_length=8, max_length=100)


class SubBody(BaseModel):
    endpoint: str = Field(min_length=20, max_length=1000)
    keys: Optional[SubKeys] = None
    user_agent: str = Field(default="", max_length=200)


@router.post("/api/push/subscribe")
def subscribe(body: SubBody, user=Depends(user_from_request)):
    if not body.endpoint.startswith("https://") or not body.keys:
        raise HTTPException(422, "Invalid push subscription")
    with connect() as db:
        db.execute("""INSERT INTO push_subs(user_id,endpoint,p256dh,auth,user_agent) VALUES(?,?,?,?,?)
                      ON CONFLICT(endpoint) DO UPDATE SET user_id=excluded.user_id, p256dh=excluded.p256dh,
                      auth=excluded.auth, user_agent=excluded.user_agent""",
                   (user["id"], body.endpoint, body.keys.p256dh, body.keys.auth, body.user_agent[:200]))
        db.execute("UPDATE users SET notify_push=1 WHERE id=?", (user["id"],))
        db.commit()
    return {"ok": True}


class UnsubBody(BaseModel):
    endpoint: str = Field(min_length=20, max_length=1000)


@router.delete("/api/push/subscribe")
def unsubscribe(body: UnsubBody, user=Depends(user_from_request)):
    with connect() as db:
        db.execute("DELETE FROM push_subs WHERE endpoint=? AND user_id=?", (body.endpoint, user["id"]))
        db.commit()
    return {"ok": True}


@router.post("/api/notify/test")
def send_test(user=Depends(user_from_request)):
    security.limit(f"notifytest:{user['id']}", 3, 60, "Test alerts are limited to 3 a minute.")
    with connect() as db:
        return notifier.run_test(db, user["id"])


@router.get("/api/admin/outbox")
def outbox(user=Depends(only("admin"))):
    with connect() as db:
        items = rows(db.execute("""SELECT o.id, o.created_at, o.event, o.channel, o.to_addr, o.subject, o.status, o.error,
                                   u.name AS user_name, u.role AS user_role FROM outbox o LEFT JOIN users u ON u.id=o.user_id
                                   ORDER BY o.id DESC LIMIT 80"""))
        counts = {r["status"]: r["n"] for r in db.execute(
            "SELECT status, COUNT(*) AS n FROM outbox WHERE created_at >= datetime('now','-7 days') GROUP BY status")}
        devices = db.execute("SELECT COUNT(*) FROM push_subs").fetchone()[0]
    return {"channels": notifier.status(), "items": items, "counts_7d": counts, "push_devices": devices,
            "scheduler": os.getenv("HEMOLINK_SCHEDULER", "on") != "off"}


# ---------------------------------------------------------------- scheduled jobs


def run_due_jobs() -> dict:
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    today = date.today().isoformat()
    sent = {"reminders": 0, "eligible_again": 0}
    with connect() as db:
        due = rows(db.execute("""SELECT a.id, a.donor_id, c.title, c.venue, s.start_time FROM appointments a
                                 JOIN slots s ON s.id=a.slot_id JOIN campaigns c ON c.id=s.campaign_id
                                 WHERE a.status='confirmed' AND a.reminded_at IS NULL AND c.event_date=?""", (tomorrow,)))
        for a in due:
            notifier.event(db, a["donor_id"], "reminder", url="/#bookings", campaign=a["title"], venue=a["venue"],
                           time=a["start_time"])
            db.execute("UPDATE appointments SET reminded_at=CURRENT_TIMESTAMP WHERE id=?", (a["id"],))
            sent["reminders"] += 1
        for u in rows(db.execute("""SELECT u.id, u.sex, u.eligible_notice_for, MAX(d.donated_on) AS last FROM users u
                                    JOIN donations d ON d.donor_id=u.id WHERE u.role='donor' AND u.is_synthetic=0
                                    GROUP BY u.id""")):
            interval = eligibility.interval_days(u["sex"])
            ready = (date.fromisoformat(u["last"]) + timedelta(days=interval)).isoformat()
            if ready <= today and u["eligible_notice_for"] != u["last"] and ready >= (date.today() - timedelta(days=3)).isoformat():
                notifier.event(db, u["id"], "eligible_again", url="/#campaigns", days=interval)
                db.execute("UPDATE users SET eligible_notice_for=? WHERE id=?", (u["last"], u["id"]))
                sent["eligible_again"] += 1
        db.commit()
    from privacy_routes import run_retention
    sent.update(run_retention())
    return sent


@router.post("/api/admin/jobs/run")
def run_jobs(user=Depends(only("admin"))):
    return run_due_jobs()


async def _scheduler_loop() -> None:
    await asyncio.sleep(20)
    while True:
        try:
            await asyncio.to_thread(run_due_jobs)
        except Exception as exc:  # never crash the app because of a job
            print("scheduler error:", exc)
        await asyncio.sleep(15 * 60)


def start_scheduler(app) -> None:
    if os.getenv("HEMOLINK_SCHEDULER", "on") == "off":
        return

    @app.on_event("startup")
    async def _start():  # noqa: ANN202
        asyncio.get_running_loop().create_task(_scheduler_loop())


@router.get("/sw.js", include_in_schema=False)
def service_worker():
    return FileResponse(ROOT / "static" / "sw.js", media_type="application/javascript",
                        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"})
