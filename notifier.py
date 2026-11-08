"""
HemoLink notifications — in-app + email + SMS + web push, in English or Bahasa Malaysia.

    event(db, user_id, "urgent_alert", blood_type="O-", units=3, centre="…", needed_by="…", url="/#notifications")

1. Writes the in-app notification (in the user's language) inside the caller's transaction.
2. Queues outside delivery on a background thread, following the user's preferences:
     email — SMTP (any provider: Gmail app password, Outlook, SendGrid SMTP, Mailtrap…)   SMTP_HOST, SMTP_FROM …
     SMS   — Twilio REST API (also WhatsApp with a "whatsapp:" sender)                     TWILIO_ACCOUNT_SID …
     push  — Web Push with VAPID keys (works on Android, desktop, and iPhone home-screen apps); keys are
             generated automatically on first start unless VAPID_PRIVATE_KEY is set.
   A channel that isn't configured is logged as "simulated" so the delivery log still shows what would be sent.
3. Every attempt is written to the `outbox` table (admin → Notifications → Delivery log).
Synthetic demo donors never receive outside messages.
"""
from __future__ import annotations

import base64
import json
import os
from contextlib import contextmanager
import re
import smtplib
import sqlite3
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

import httpx

DB_PATH = Path(os.environ.get("HEMOLINK_DB_PATH", Path(__file__).resolve().parent / "hemolink_v2.db"))
APP_URL = os.environ.get("HEMOLINK_APP_URL", "http://localhost:8000").rstrip("/")
_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="notify")
_futures: list[Future] = []
_lock = threading.Lock()

# ---------------------------------------------------------------- templates (English / Bahasa Malaysia)

T = {
    "urgent_alert": {
        "en": ("Urgent: {blood_type} blood needed", "{centre} needs {units} units of {blood_type} by {needed_by}. You're a "
               "close match — can you come? Reply in HemoLink."),
        "ms": ("Segera: Darah {blood_type} diperlukan", "{centre} memerlukan {units} unit darah {blood_type} sebelum "
               "{needed_by}. Anda padanan yang sesuai — boleh datang? Balas dalam HemoLink."),
        "channels": ["email", "sms", "push"],
    },
    "booking_confirmed": {
        "en": ("Appointment confirmed", "{campaign} · {date} at {time}. Eat well, drink water and bring your IC."),
        "ms": ("Temujanji disahkan", "{campaign} · {date} pada {time}. Makan dengan baik, minum air dan bawa IC anda."),
        "channels": ["email", "push"],
    },
    "booking_cancelled": {
        "en": ("Appointment cancelled", "Your appointment for {campaign} was cancelled."),
        "ms": ("Temujanji dibatalkan", "Temujanji anda untuk {campaign} telah dibatalkan."),
        "channels": [],
    },
    "reminder": {
        "en": ("Reminder: donation tomorrow", "{campaign} at {venue}, {time} tomorrow. Sleep well, eat a proper meal and "
               "drink 2–3 glasses of water."),
        "ms": ("Peringatan: derma darah esok", "{campaign} di {venue}, {time} esok. Tidur cukup, makan dengan baik dan "
               "minum 2–3 gelas air."),
        "channels": ["email", "sms", "push"],
    },
    "organizer_booking": {
        "en": ("New booking", "{donor} booked {campaign} at {time} ({booked}/{capacity} slots filled)."),
        "ms": ("Tempahan baharu", "{donor} menempah {campaign} pada {time} ({booked}/{capacity} slot diisi)."),
        "channels": ["push"],
    },
    "organizer_cancel": {
        "en": ("Booking cancelled", "{donor} cancelled their {time} slot at {campaign}."),
        "ms": ("Tempahan dibatalkan", "{donor} membatalkan slot {time} di {campaign}."),
        "channels": [],
    },
    "alert_reply": {
        "en": ("Donor coming: {blood_type}", "{donor} said yes to the {blood_type} request ({yes} of {needed} so far)."),
        "ms": ("Penderma akan datang: {blood_type}", "{donor} bersetuju untuk permintaan {blood_type} ({yes} daripada "
               "{needed} setakat ini)."),
        "channels": ["push"],
    },
    "donation_recorded": {
        "en": ("Thank you for donating", "Your donation at {place} is recorded. You can donate again from {next_date}."),
        "ms": ("Terima kasih kerana menderma", "Derma anda di {place} telah direkodkan. Anda boleh menderma semula mulai "
               "{next_date}."),
        "channels": ["email", "push"],
    },
    "role_change": {
        "en": ("Organizer access {status}", "{message}"),
        "ms": ("Akses penganjur {status_ms}", "{message_ms}"),
        "channels": ["email", "push"],
    },
    "new_campaign_nearby": {
        "en": ("New blood drive near you", "{campaign} · {date} at {venue}, {city} ({km} km away). Book a slot in HemoLink."),
        "ms": ("Kempen derma darah berhampiran", "{campaign} · {date} di {venue}, {city} ({km} km dari anda). Tempah slot "
               "dalam HemoLink."),
        "channels": ["push", "email"],
    },
    "eligible_again": {
        "en": ("You can donate again", "It's been {days} days since your last donation — you're eligible from today. "
               "Find a drive near you in HemoLink."),
        "ms": ("Anda boleh menderma semula", "Sudah {days} hari sejak derma terakhir anda — anda layak mulai hari ini. "
               "Cari kempen berhampiran dalam HemoLink."),
        "channels": ["push", "email"],
    },
    "feedback": {
        "en": ("New rating: {rating}★", "{campaign}: \"{comment}\""),
        "ms": ("Penilaian baharu: {rating}★", "{campaign}: \"{comment}\""),
        "channels": [],
    },
    "test": {
        "en": ("Test alert from HemoLink", "If you can read this, {channel} alerts are working."),
        "ms": ("Makluman ujian daripada HemoLink", "Jika anda boleh membaca ini, makluman {channel} berfungsi."),
        "channels": ["email", "sms", "push"],
    },
}


class _Safe(dict):
    def __missing__(self, key):
        return ""


def render(event: str, lang: str, data: dict) -> tuple[str, str]:
    tpl = T[event].get(lang) or T[event]["en"]
    d = _Safe({k: ("" if v is None else v) for k, v in data.items()})
    return tpl[0].format_map(d), tpl[1].format_map(d)


# ---------------------------------------------------------------- channels


def email_configured() -> bool:
    return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_FROM"))


def sms_configured() -> bool:
    return bool(os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN")
                and (os.getenv("TWILIO_FROM") or os.getenv("TWILIO_MESSAGING_SERVICE_SID")))


def push_available() -> bool:
    try:
        import pywebpush  # noqa: F401
    except ImportError:
        return False
    return vapid_public_key() is not None


def status() -> dict:
    return {
        "email": {"live": email_configured(), "detail": os.getenv("SMTP_HOST") or "not configured — simulated"},
        "sms": {"live": sms_configured(), "detail": "Twilio" if sms_configured() else "not configured — simulated"},
        "push": {"live": push_available(), "detail": "Web Push (VAPID)" if push_available() else "pywebpush not installed"},
        "app_url": APP_URL,
    }


def normalise_phone(raw: str) -> str | None:
    """Malaysian-friendly: 012-345 6789 → +60123456789. Returns None if it doesn't look like a phone number."""
    digits = re.sub(r"[^\d+]", "", raw or "")
    if not digits:
        return None
    if digits.startswith("+"):
        num = "+" + re.sub(r"\D", "", digits)
    elif digits.startswith("60"):
        num = "+" + digits
    elif digits.startswith("0"):
        num = "+60" + digits[1:]
    else:
        num = "+" + digits
    return num if 10 <= len(num) <= 16 else None


def mask(addr: str | None) -> str:
    if not addr:
        return ""
    if "@" in addr:
        name, dom = addr.split("@", 1)
        return (name[:1] + "***@" + dom) if name else "***@" + dom
    if addr.startswith("https://"):
        return re.sub(r"^https://([^/]+)/.*$", r"\1/…", addr)
    return addr[:5] + "****" + addr[-3:] if len(addr) > 8 else "****"


def _send_email(to: str, subject: str, body: str, url: str, lang: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.environ["SMTP_FROM"]
    msg["To"] = to
    link = APP_URL + (url or "/")
    foot = ("Tukar tetapan makluman dalam Profil Saya." if lang == "ms" else "Change your alert settings in My Profile.")
    msg.set_content(f"{subject}\n\n{body}\n\n{link}\n\n— HemoLink\n{foot}")
    msg.add_alternative(f"""<div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;border:2px solid #3b2420;border-radius:16px;overflow:hidden">
<div style="background:#b3202e;color:#fff;padding:16px 20px;font-weight:700;font-size:18px">HemoLink</div>
<div style="padding:20px;color:#3b2420;background:#fffdf9"><h2 style="margin:0 0 10px;font-size:19px">{subject}</h2>
<p style="line-height:1.6;margin:0 0 18px">{body}</p><a href="{link}" style="background:#b3202e;color:#fff;padding:10px 18px;border-radius:999px;text-decoration:none;font-weight:700">{"Buka HemoLink" if lang == "ms" else "Open HemoLink"}</a>
<p style="color:#9b8577;font-size:12px;margin-top:22px">{foot}</p></div></div>""", subtype="html")
    port = int(os.getenv("SMTP_PORT", "587"))
    user, pwd = os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD")
    if port == 465:
        with smtplib.SMTP_SSL(os.environ["SMTP_HOST"], port, timeout=20) as s:
            if user:
                s.login(user, pwd or "")
            s.send_message(msg)
    else:
        with smtplib.SMTP(os.environ["SMTP_HOST"], port, timeout=20) as s:
            if os.getenv("SMTP_STARTTLS", "1") != "0":
                s.starttls()
            if user:
                s.login(user, pwd or "")
            s.send_message(msg)


def _send_sms(to: str, text: str) -> None:
    sid, token = os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"]
    data = {"To": to, "Body": text[:600]}
    sender = os.getenv("TWILIO_FROM", "")
    if sender.startswith("whatsapp:"):
        data["To"] = "whatsapp:" + to
    if os.getenv("TWILIO_MESSAGING_SERVICE_SID"):
        data["MessagingServiceSid"] = os.environ["TWILIO_MESSAGING_SERVICE_SID"]
    else:
        data["From"] = sender
    r = httpx.post(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json", data=data, auth=(sid, token),
                   timeout=20)
    if r.status_code >= 300:
        raise RuntimeError(f"Twilio HTTP {r.status_code}: {r.json().get('message', '')[:120] if r.content else ''}")


# ---------------------------------------------------------------- web push (VAPID)


def _vapid_file() -> Path:
    return DB_PATH.parent / "vapid_private.pem"


def _vapid():
    from py_vapid import Vapid01
    pem = os.getenv("VAPID_PRIVATE_KEY")
    if pem:
        return Vapid01.from_pem(pem.replace("\\n", "\n").encode())
    f = _vapid_file()
    if f.exists():
        return Vapid01.from_file(str(f))
    v = Vapid01()
    v.generate_keys()
    f.parent.mkdir(parents=True, exist_ok=True)
    v.save_key(str(f))
    return v


def vapid_public_key() -> str | None:
    try:
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
        raw = _vapid().public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
    except Exception:
        return None
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _send_push(sub: dict, payload: dict) -> int:
    from pywebpush import WebPushException, webpush
    try:
        webpush(subscription_info={"endpoint": sub["endpoint"], "keys": {"p256dh": sub["p256dh"], "auth": sub["auth"]}},
                data=json.dumps(payload), vapid_private_key=_vapid(),
                vapid_claims={"sub": os.getenv("VAPID_SUBJECT", "mailto:admin@hemolink.example")}, ttl=6 * 3600,
                timeout=15)
        return 201
    except WebPushException as exc:
        code = exc.response.status_code if exc.response is not None else 0
        if code in (404, 410):
            return code  # subscription expired → caller deletes it
        raise RuntimeError(f"Push service HTTP {code}") from exc


# ---------------------------------------------------------------- delivery


@contextmanager
def _conn():
    c = sqlite3.connect(DB_PATH, timeout=20)
    c.row_factory = sqlite3.Row
    try:
        yield c
    finally:
        c.close()


def _log(c, user_id, event, channel, to, subject, status_, error=None):
    c.execute("""INSERT INTO outbox(user_id,event,channel,to_addr,subject,status,error) VALUES(?,?,?,?,?,?,?)""",
              (user_id, event, channel, mask(to), subject[:160], status_, (error or "")[:300]))


def _deliver(user_id: int, event: str, subject: str, body: str, url: str, lang: str, channels: list[str],
             title_for_test: str | None = None) -> None:
    with _conn() as c:
        u = c.execute("SELECT email, phone FROM users WHERE id=?", (user_id,)).fetchone()
        if not u:
            return
        for ch in channels:
            try:
                if ch == "email":
                    if email_configured():
                        _send_email(u["email"], subject, body, url, lang)
                        _log(c, user_id, event, "email", u["email"], subject, "sent")
                    else:
                        _log(c, user_id, event, "email", u["email"], subject, "simulated")
                elif ch == "sms":
                    phone = normalise_phone(u["phone"] or "")
                    if not phone:
                        _log(c, user_id, event, "sms", None, subject, "skipped", "no valid phone number in profile")
                    elif sms_configured():
                        _send_sms(phone, f"HemoLink: {subject}. {body}")
                        _log(c, user_id, event, "sms", phone, subject, "sent")
                    else:
                        _log(c, user_id, event, "sms", phone, subject, "simulated")
                elif ch == "push":
                    subs = c.execute("SELECT * FROM push_subs WHERE user_id=?", (user_id,)).fetchall()
                    if not subs and event == "test":
                        _log(c, user_id, event, "push", None, subject, "skipped", "push not enabled on this account yet")
                    for s in subs:
                        code = _send_push(dict(s), {"title": subject, "body": body, "url": url or "/", "tag": event})
                        if code in (404, 410):
                            c.execute("DELETE FROM push_subs WHERE id=?", (s["id"],))
                            _log(c, user_id, event, "push", s["endpoint"], subject, "failed", "device unsubscribed (removed)")
                        else:
                            _log(c, user_id, event, "push", s["endpoint"], subject, "sent")
            except Exception as exc:  # one failing channel never blocks the others
                _log(c, user_id, event, ch, None, subject, "failed", str(exc))
        c.commit()


def _submit(db, *args) -> None:
    # Inline only when asked and safe: inside an open write transaction the delivery thread must wait for the
    # commit (it logs to the outbox on its own connection), otherwise SQLite would block on our own lock.
    if os.getenv("HEMOLINK_NOTIFY_SYNC") == "1" and not db.in_transaction:
        _deliver(*args)
        return
    with _lock:
        _futures.append(_pool.submit(_deliver, *args))
        _futures[:] = [f for f in _futures if not f.done()]


def wait_idle(timeout: float = 10.0) -> None:
    """Tests / scripts: wait until queued deliveries finish."""
    with _lock:
        pending = list(_futures)
    for f in pending:
        f.result(timeout=timeout)


def prefs(db, user_id: int):
    return db.execute("""SELECT id, role, is_synthetic, lang, notify_email, notify_sms, notify_push, notify_nearby
                         FROM users WHERE id=?""", (user_id,)).fetchone()


def event(db, user_id: int, name: str, url: str = "/", in_app: bool = True, channels: list[str] | None = None,
          **data) -> None:
    """Create the in-app notification now and queue outside delivery per the user's preferences."""
    u = prefs(db, user_id)
    if not u:
        return
    lang = u["lang"] if u["lang"] in ("en", "ms") else "en"
    title, body = render(name, lang, data)
    if in_app:
        db.execute("INSERT INTO notifications(user_id,title,body) VALUES(?,?,?)", (user_id, title, body))
    if u["is_synthetic"]:
        return
    wanted = channels if channels is not None else T[name]["channels"]
    allowed = [ch for ch in wanted if (ch == "email" and u["notify_email"]) or (ch == "sms" and u["notify_sms"])
               or (ch == "push" and u["notify_push"])]
    if allowed:
        _submit(db, user_id, name, title, body, url, lang, allowed)


def run_test(db, user_id: int) -> dict:
    u = prefs(db, user_id)
    lang = u["lang"] if u and u["lang"] in ("en", "ms") else "en"
    for ch in ("email", "sms", "push"):
        title, body = render("test", lang, {"channel": {"email": "email", "sms": "SMS", "push": "push"}[ch]})
        _submit(db, user_id, "test", title, body, "/", lang, [ch])
    return {"queued": ["email", "sms", "push"], "at": datetime.now().isoformat(timespec="seconds")}
