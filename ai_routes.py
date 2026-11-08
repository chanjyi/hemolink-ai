"""
HemoLink AI v2 — AI feature endpoints (added on top of the v1 app).

  * Shortage outlook ............ GET  /api/outlook
  * Urgent requests + matching .. GET/POST /api/requests, /api/requests/{id}[/alerts|/simulate|/close]
  * Donor alerts ................ GET  /api/my-alerts, POST /api/alerts/{id}/respond, /api/alerts/{id}/donated
  * Eligibility check ........... GET  /api/eligibility, POST /api/eligibility/check
  * Feedback & check-in ......... POST /api/feedback, /api/organizer/bookings/{id}/status
  * Reports & models ............ GET  /api/reports (organizer), GET /api/models (admin)
"""
from __future__ import annotations

import json
import random
from datetime import date, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ai import assistant as ai_assistant
from ai import churn, eligibility, llm, matching, stock
from ai.hemocare import meds
import notifier
import security
from ai.schemas import (
    Alert,
    AssistantRequest,
    Centre,
    ChatMessage,
    DonorHealth,
    MatchRequest,
    Profile,
    UrgentRequest,
)
from ai.util import first_name, haversine_km
from app import connect, only, rows, user_from_request
from seed import BLOOD_TYPES

router = APIRouter(prefix="/api")
DATA_NOTE = (
    "Stock movements, donors and replies are SIMULATED for this prototype. The public MOH dataset reports "
    "donations collected only — not hospital usage or live stock."
)


def today() -> str:
    return date.today().isoformat()


def privacy_name(name: str) -> str:
    first, *rest = name.split(" ")
    return " ".join([first] + [r[0] + "." for r in rest if r])


# ---------------------------------------------------------------- data loading


def load_people(db):
    """Users as AI-module inputs. Donors need a known blood type, birth year and weight to be matched."""
    users = {u["id"]: u for u in rows(db.execute(
        "SELECT id,name,role,blood_type,city,lat,lng,birth_year,weight_kg,sex,no_shows,is_synthetic FROM users"))}
    donations: dict[int, list[str]] = {}
    for donor_id, day in db.execute("SELECT donor_id, donated_on FROM donations ORDER BY donated_on"):
        donations.setdefault(donor_id, []).append(day)
    profiles, health = [], []
    holds = medicine_holds(db)
    for u in users.values():
        if u["lat"] is None or u["lng"] is None:
            continue
        profiles.append(Profile(id=str(u["id"]), role=u["role"], name=u["name"], area=u["city"] or "", lat=u["lat"], lng=u["lng"]))
        if u["role"] == "donor" and u["blood_type"] in BLOOD_TYPES and u["birth_year"] and u["weight_kg"]:
            health.append(DonorHealth(
                donor_id=str(u["id"]), blood_type=u["blood_type"], birth_year=u["birth_year"],
                weight_kg=u["weight_kg"], sex=u["sex"], donations=donations.get(u["id"], []), no_shows=u["no_shows"] or 0,
                **hold_fields(holds.get(u["id"])),
            ))
    return profiles, health, users


def donor_interval(db, donor_id: int) -> int:
    row = db.execute("SELECT sex FROM users WHERE id=?", (donor_id,)).fetchone()
    return eligibility.interval_days(row["sex"] if row else None)


def user_sex(user_id: int):
    with connect() as db:
        row = db.execute("SELECT sex FROM users WHERE id=?", (user_id,)).fetchone()
    return row["sex"] if row else None


def load_alerts(db) -> list[Alert]:
    return [
        Alert(id=str(a["id"]), request_id=str(a["request_id"]), donor_id=str(a["donor_id"]), score=a["score"],
              sent_at=a["sent_at"], response=a["response"])
        for a in rows(db.execute("SELECT id,request_id,donor_id,score,sent_at,response FROM alerts"))
    ]


def load_centres(db) -> list[Centre]:
    return [Centre(id=c["id"], name=c["name"], area=c["city"], lat=c["lat"], lng=c["lng"])
            for c in rows(db.execute("SELECT * FROM centres"))]


def my_health(db, user) -> DonorHealth:
    u = db.execute("SELECT blood_type,birth_year,weight_kg,sex,no_shows FROM users WHERE id=?", (user["id"],)).fetchone()
    if u["blood_type"] not in BLOOD_TYPES or not u["birth_year"] or not u["weight_kg"]:
        raise HTTPException(422, "Please add your blood type, birth year and weight in My Profile first.")
    days = [r[0] for r in db.execute("SELECT donated_on FROM donations WHERE donor_id=? ORDER BY donated_on", (user["id"],))]
    return DonorHealth(donor_id=str(user["id"]), blood_type=u["blood_type"], birth_year=u["birth_year"],
                       weight_kg=u["weight_kg"], sex=u["sex"], donations=days, no_shows=u["no_shows"] or 0,
                       **hold_fields(medicine_holds(db).get(user["id"])))


def medicine_holds(db) -> dict[int, dict]:
    """HemoCare medicine waiting periods per donor (only real donors keep a medicine list)."""
    by_user: dict[int, list[dict]] = {}
    for m in rows(db.execute("SELECT user_id, name, category, end_date FROM hemo_meds")):
        by_user.setdefault(m["user_id"], []).append(m)
    return {uid: h for uid, ms in by_user.items() if (h := meds.hold(ms))}


def hold_fields(h: dict | None) -> dict:
    if not h:
        return {}
    return {"medicine_hold_until": h["until"], "medicine_hold_ongoing": h["ongoing"], "medicine_hold_reason": h["reason"]}


def notify(db, user_id: int, title: str, body: str) -> None:
    db.execute("INSERT INTO notifications(user_id,title,body) VALUES(?,?,?)", (user_id, title, body))


# ---------------------------------------------------------------- 1. shortage outlook

_fit_cache: dict = {"key": None, "fits": {}}


def outlook(db) -> list[dict]:
    key = tuple(db.execute("SELECT COUNT(*), MAX(date) FROM stock_history").fetchone())
    if _fit_cache["key"] != key:
        hist = rows(db.execute("SELECT date,blood_type,collected,used FROM stock_history ORDER BY date"))
        fits = {}
        for t in BLOOD_TYPES:
            try:
                fits[t] = stock.fit_type(hist, t)
            except ValueError:
                pass  # not enough history for this type
        _fit_cache.update(key=key, fits=fits)
    out = []
    for inv in rows(db.execute("SELECT blood_type,units,threshold FROM inventory")):
        fit = _fit_cache["fits"].get(inv["blood_type"])
        if not fit:
            continue
        out.append({
            "blood_type": inv["blood_type"],
            **stock.project(fit, inv["units"], inv["threshold"]),
            "avg_daily_use": fit["avg_daily_use"],
            "supply_trend_pct": fit["supply_trend_pct"],
            "metrics": fit["metrics"],
            "recent": fit["recent"],
        })
    out.sort(key=lambda x: BLOOD_TYPES.index(x["blood_type"]))
    return out


def most_urgent(types: list[dict]) -> dict | None:
    if not types:
        return None
    return sorted(types, key=lambda x: (stock.STATUS_ORDER[x["status"]], x["days_of_supply"]))[0]


@router.get("/outlook")
def get_outlook(user=Depends(user_from_request)):
    with connect() as db:
        types = outlook(db)
    return {"types": types, "most_urgent": most_urgent(types), "note": DATA_NOTE,
            "model": "Random Forest (collected) + Random Forest (used) → 7-day stock projection"}


# ---------------------------------------------------------------- 2. urgent requests + matching


class RequestBody(BaseModel):
    blood_type: str
    units: int = Field(ge=1, le=100)
    needed_by: date
    note: str = Field(default="", max_length=200)


class RespondBody(BaseModel):
    response: Literal["yes", "no"]


def get_request(db, request_id: int, user) -> dict:
    r = db.execute("""SELECT r.*, c.name AS centre_name, c.city AS centre_city, c.lat, c.lng
                      FROM urgent_requests r JOIN centres c ON c.id=r.centre_id WHERE r.id=?""", (request_id,)).fetchone()
    if not r:
        raise HTTPException(404, "Request not found")
    return dict(r)


def run_match(db, r: dict):
    profiles, health, users = load_people(db)
    req = UrgentRequest(id=str(r["id"]), centre_id=r["centre_id"], blood_type=r["blood_type"], units=r["units"],
                        needed_by=r["needed_by"], note=r["note"], status=r["status"], created_at=r["created_at"])
    centre = Centre(id=r["centre_id"], name=r["centre_name"], area=r["centre_city"], lat=r["lat"], lng=r["lng"])
    result = matching.match_donors(MatchRequest(today=today(), request=req, centre=centre, profiles=profiles,
                                                health=health, alerts=load_alerts(db)))
    return result, users


@router.get("/requests")
def list_requests(user=Depends(only("admin"))):
    with connect() as db:
        where, args = "", ()
        items = rows(db.execute(f"""SELECT r.*, c.name AS centre_name,
              (SELECT COUNT(*) FROM alerts a WHERE a.request_id=r.id) AS alerted,
              (SELECT COUNT(*) FROM alerts a WHERE a.request_id=r.id AND a.response='yes') AS said_yes,
              (SELECT COUNT(*) FROM alerts a WHERE a.request_id=r.id AND a.donated=1) AS donated
              FROM urgent_requests r JOIN centres c ON c.id=r.centre_id {where}
              ORDER BY (r.status='open') DESC, r.created_at DESC, r.id DESC LIMIT 30""", args))
    return items


@router.post("/requests")
def create_request(body: RequestBody, user=Depends(only("admin"))):
    if body.blood_type not in BLOOD_TYPES:
        raise HTTPException(422, "Invalid blood type")
    if body.needed_by < date.today():
        raise HTTPException(422, "Needed-by date must be today or later")
    with connect() as db:
        centre_id = user.get("centre_id") or db.execute("SELECT id FROM centres ORDER BY id LIMIT 1").fetchone()["id"]
        rid = db.execute(
            "INSERT INTO urgent_requests(centre_id,blood_type,units,needed_by,note,created_by,created_at) VALUES(?,?,?,?,?,?,?)",
            (centre_id, body.blood_type, body.units, body.needed_by.isoformat(), body.note.strip(), user["id"], today()),
        ).lastrowid
        db.commit()
    return {"id": rid}


@router.get("/requests/{request_id}")
def request_detail(request_id: int, user=Depends(only("admin"))):
    with connect() as db:
        r = get_request(db, request_id, user)
        result, users = run_match(db, r)
        sent = rows(db.execute("""SELECT a.id,a.donor_id,a.score,a.response,a.donated,u.name,u.blood_type,u.is_synthetic
                                  FROM alerts a JOIN users u ON u.id=a.donor_id WHERE a.request_id=?
                                  ORDER BY (a.response='yes') DESC, a.score DESC""", (request_id,)))
    candidates = []
    for c in result.candidates[:25]:
        u = users[int(c.donor_id)]
        candidates.append({"donor_id": int(c.donor_id), "name": privacy_name(u["name"]), "blood_type": u["blood_type"],
                           "km": round(c.km, 1), "score": c.score, "p_yes": c.p_yes, "reasons": c.reasons,
                           "selected": c.selected})
    for a in sent:
        a["name"] = privacy_name(a["name"])
    return {
        "request": r,
        "match": {"candidates": candidates, "total_candidates": len(result.candidates),
                  "selected_count": result.selected_count, "expected_yes": result.expected_yes,
                  "excluded": result.excluded.model_dump()},
        "alerts": sent,
        "summary": {"alerted": len(sent), "yes": sum(a["response"] == "yes" for a in sent),
                    "no": sum(a["response"] == "no" for a in sent), "donated": sum(a["donated"] for a in sent)},
    }


@router.post("/requests/{request_id}/alerts")
def send_alerts(request_id: int, user=Depends(only("admin"))):
    with connect() as db:
        r = get_request(db, request_id, user)
        if r["status"] != "open":
            raise HTTPException(409, "This request is closed")
        result, _ = run_match(db, r)
        sent = 0
        for c in result.candidates:
            if not c.selected:
                continue
            cur = db.execute("INSERT OR IGNORE INTO alerts(request_id,donor_id,score,reasons,sent_at) VALUES(?,?,?,?,?)",
                             (request_id, int(c.donor_id), c.score, json.dumps(c.reasons), today()))
            if cur.rowcount:
                sent += 1
                notifier.event(db, int(c.donor_id), "urgent_alert", url="/#notifications", blood_type=r["blood_type"],
                               units=r["units"], centre=r["centre_name"], needed_by=r["needed_by"])
        db.commit()
    return {"sent": sent}


@router.post("/requests/{request_id}/simulate")
def simulate_replies(request_id: int, user=Depends(only("admin"))):
    """Demo helper: synthetic donors reply according to their AI score. Real accounts are never touched."""
    with connect() as db:
        get_request(db, request_id, user)
        pending = rows(db.execute("""SELECT a.id,a.score FROM alerts a JOIN users u ON u.id=a.donor_id
                                     WHERE a.request_id=? AND a.response IS NULL AND u.is_synthetic=1""", (request_id,)))
        rnd = random.Random(request_id * 97 + len(pending))
        replied = 0
        for a in pending:
            if rnd.random() < 0.8:
                answer = "yes" if rnd.random() < min(0.9, a["score"] / 110) else "no"
                db.execute("UPDATE alerts SET response=?, responded_at=? WHERE id=?", (answer, today(), a["id"]))
                replied += 1
        db.commit()
    return {"replied": replied}


@router.post("/requests/{request_id}/close")
def close_request(request_id: int, user=Depends(only("admin"))):
    with connect() as db:
        get_request(db, request_id, user)
        db.execute("UPDATE urgent_requests SET status='closed' WHERE id=? AND status='open'", (request_id,))
        db.commit()
    return {"ok": True}


@router.post("/alerts/{alert_id}/donated")
def mark_donated(alert_id: int, user=Depends(only("admin"))):
    with connect() as db:
        a = db.execute("""SELECT a.*, u.blood_type FROM alerts a JOIN users u ON u.id=a.donor_id WHERE a.id=?""", (alert_id,)).fetchone()
        if not a:
            raise HTTPException(404, "Alert not found")
        r = get_request(db, a["request_id"], user)
        if a["response"] != "yes" or a["donated"]:
            raise HTTPException(409, "Only donors who said yes and have not donated yet can be marked")
        db.execute("UPDATE alerts SET donated=1 WHERE id=?", (alert_id,))
        db.execute("INSERT INTO donations(donor_id,donated_on,source) VALUES(?,?,'urgent request')", (a["donor_id"], today()))
        db.execute("UPDATE inventory SET units=units+1, updated_at=CURRENT_TIMESTAMP WHERE blood_type=?", (a["blood_type"],))
        done = db.execute("SELECT COUNT(*) FROM alerts WHERE request_id=? AND donated=1", (r["id"],)).fetchone()[0]
        if done >= r["units"]:
            db.execute("UPDATE urgent_requests SET status='fulfilled' WHERE id=?", (r["id"],))
        notifier.event(db, a["donor_id"], "donation_recorded", place=r["centre_name"],
                       next_date=(date.today() + timedelta(days=donor_interval(db, a["donor_id"]))).isoformat())
        db.commit()
    return {"ok": True}


@router.get("/my-alerts")
def my_alerts(user=Depends(only("donor"))):
    with connect() as db:
        items = rows(db.execute("""SELECT a.id,a.response,a.donated,a.reasons,a.sent_at,r.blood_type,r.units,r.needed_by,
              r.note,r.status,c.name AS centre_name,c.city AS centre_city
              FROM alerts a JOIN urgent_requests r ON r.id=a.request_id JOIN centres c ON c.id=r.centre_id
              WHERE a.donor_id=? AND (r.status='open' OR a.sent_at>=?) ORDER BY a.sent_at DESC, a.id DESC""",
                                (user["id"], (date.today() - timedelta(days=7)).isoformat())))
    for a in items:
        a["reasons"] = json.loads(a["reasons"] or "[]")
        a["code"] = f"HL-{a['id']:05d}"
    return items


@router.post("/alerts/{alert_id}/respond")
def respond(alert_id: int, body: RespondBody, user=Depends(only("donor"))):
    with connect() as db:
        cur = db.execute("""UPDATE alerts SET response=?, responded_at=? WHERE id=? AND donor_id=?
                            AND request_id IN (SELECT id FROM urgent_requests WHERE status='open')""",
                         (body.response, today(), alert_id, user["id"]))
        if not cur.rowcount:
            raise HTTPException(404, "Alert not found or request already closed")
        if body.response == "yes":  # tell the blood bank staff someone is coming
            r = db.execute("""SELECT r.id, r.blood_type, r.units FROM alerts a JOIN urgent_requests r ON r.id=a.request_id
                              WHERE a.id=?""", (alert_id,)).fetchone()
            yes = db.execute("SELECT COUNT(*) FROM alerts WHERE request_id=? AND response='yes'", (r["id"],)).fetchone()[0]
            for adm in db.execute("SELECT id FROM users WHERE role='admin' AND is_synthetic=0").fetchall():
                notifier.event(db, adm["id"], "alert_reply", url="/#requests", donor=user["name"],
                               blood_type=r["blood_type"], yes=yes, needed=r["units"])
        db.commit()
    return {"ok": True}


# ---------------------------------------------------------------- 3. eligibility


def hemoscan_hint(db, user_id: int) -> dict | None:
    """Latest confirmed HemoScan haemoglobin, shown as advice next to eligibility (never changes the verdict)."""
    r = db.execute("""SELECT r.id, r.report_date, x.value FROM hemo_reports r JOIN hemo_results x ON x.report_id=r.id
                      WHERE r.user_id=? AND r.status='confirmed' AND x.biomarker='hgb'
                      ORDER BY r.report_date DESC, r.id DESC LIMIT 1""", (user_id,)).fetchone()
    if not r:
        return None
    from ai.hemoscan.rules import DONATION_HB_THRESHOLD
    age = (date.today() - date.fromisoformat(r["report_date"])).days
    ok = r["value"] >= DONATION_HB_THRESHOLD
    return {"report_id": r["id"], "report_date": r["report_date"], "hb": r["value"], "ok": ok, "days_old": age,
            "message": (f"Your HemoScan report from {r['report_date']} shows haemoglobin {r['value']:g} g/dL"
                        + (" — fine for donating; it is re-checked on the day." if ok else
                           f", below the typical {DONATION_HB_THRESHOLD:g} g/dL minimum. Please speak to a doctor before booking."))}


class CheckBody(BaseModel):
    answers: dict[str, bool] = Field(default_factory=dict)


@router.get("/eligibility")
def eligibility_info(user=Depends(only("donor"))):
    rules = eligibility.RULES
    with connect() as db:
        try:
            h = my_health(db, user)
            status = eligibility.evaluate(h, today()).model_dump()
        except HTTPException:
            status = None
        hb = hemoscan_hint(db, user["id"])
    return {"questions": [{"id": q["id"], "text": q["text"]} for q in rules["questions"]],
            "note": rules["sourceNote"], "status": status, "hemoscan": hb,
            "labels": eligibility.VERDICT_LABEL, "interval_days": eligibility.interval_days(user_sex(user["id"])),
            "sources": eligibility.SOURCES, "checked_on": rules["checkedOn"]}


@router.post("/eligibility/check")
def eligibility_check(body: CheckBody, user=Depends(only("donor"))):
    with connect() as db:
        h = my_health(db, user)
    result = eligibility.evaluate(h, today(), body.answers)
    explained = ai_assistant.explain(result, first_name(user["name"]))
    return {"result": result.model_dump(), "label": eligibility.VERDICT_LABEL[result.verdict],
            "explanation": explained.explanation, "used_llm": explained.used_llm, "note": eligibility.RULES["sourceNote"]}


# ---------------------------------------------------------------- feedback + check-in


class FeedbackBody(BaseModel):
    appointment_id: int
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=400)


class StatusBody(BaseModel):
    status: Literal["donated", "no_show"]


@router.post("/feedback")
def feedback(body: FeedbackBody, user=Depends(only("donor"))):
    with connect() as db:
        a = db.execute("""SELECT a.status, s.campaign_id FROM appointments a JOIN slots s ON s.id=a.slot_id
                          WHERE a.id=? AND a.donor_id=?""", (body.appointment_id, user["id"])).fetchone()
        if not a:
            raise HTTPException(404, "Appointment not found")
        if a["status"] != "donated":
            raise HTTPException(409, "You can rate a campaign after your donation is recorded")
        db.execute("""INSERT INTO feedback(campaign_id,donor_id,rating,comment) VALUES(?,?,?,?)
                      ON CONFLICT(campaign_id,donor_id) DO UPDATE SET rating=excluded.rating, comment=excluded.comment""",
                   (a["campaign_id"], user["id"], body.rating, body.comment.strip()))
        c = db.execute("SELECT organizer_id, title FROM campaigns WHERE id=?", (a["campaign_id"],)).fetchone()
        if c and c["organizer_id"]:
            notifier.event(db, c["organizer_id"], "feedback", url="/#reports", rating=body.rating, campaign=c["title"],
                           comment=(body.comment.strip() or "—")[:120])
        db.commit()
    return {"ok": True}


@router.post("/organizer/bookings/{appointment_id}/status")
def set_booking_status(appointment_id: int, body: StatusBody, user=Depends(only("organizer"))):
    with connect() as db:
        a = db.execute("""SELECT a.id,a.status,a.donor_id,c.organizer_id,c.title,u.blood_type FROM appointments a
                          JOIN slots s ON s.id=a.slot_id JOIN campaigns c ON c.id=s.campaign_id
                          JOIN users u ON u.id=a.donor_id WHERE a.id=?""", (appointment_id,)).fetchone()
        if not a or a["organizer_id"] != user["id"]:
            raise HTTPException(404, "Booking not found")
        if a["status"] != "confirmed":
            raise HTTPException(409, "Only confirmed bookings can be checked in")
        db.execute("UPDATE appointments SET status=? WHERE id=?", (body.status, appointment_id))
        if body.status == "donated":
            db.execute("INSERT INTO donations(donor_id,donated_on,source) VALUES(?,?,'campaign')", (a["donor_id"], today()))
            if a["blood_type"] in BLOOD_TYPES:
                db.execute("UPDATE inventory SET units=units+1, updated_at=CURRENT_TIMESTAMP WHERE blood_type=?", (a["blood_type"],))
            notifier.event(db, a["donor_id"], "donation_recorded", url="/#bookings", place=a["title"],
                           next_date=(date.today() + timedelta(days=donor_interval(db, a["donor_id"]))).isoformat())
        else:
            db.execute("UPDATE users SET no_shows=no_shows+1 WHERE id=?", (a["donor_id"],))
        db.commit()
    return {"ok": True}


# ---------------------------------------------------------------- 4. reports + return model + campaign planner

_return_cache: dict = {"key": None, "value": None}


def return_model(db):
    key = (today(),) + tuple(db.execute("SELECT COUNT(*), (SELECT SUM(no_shows) FROM users) FROM donations").fetchone())
    if _return_cache["key"] != key:
        profiles, health, users = load_people(db)
        _return_cache.update(key=key, value=(churn.train_and_score(profiles, health, load_centres(db), today()), users))
    return _return_cache["value"]


def campaign_suggestion(db, centre: dict, top: dict | None) -> dict | None:
    if not top:
        return None
    profiles, health, users = load_people(db)
    compatible = matching.COMPATIBLE_DONORS[top["blood_type"]]
    counts: dict[str, int] = {}
    for h in health:
        u = users[int(h.donor_id)]
        if h.blood_type not in compatible or haversine_km(u["lat"], u["lng"], centre["lat"], centre["lng"]) > 25:
            continue
        if eligibility.is_basically_eligible(h, today()):
            counts[u["city"]] = counts.get(u["city"], 0) + 1
    if not counts:
        return None
    city, n = max(counts.items(), key=lambda kv: kv[1])
    by_weekday = [0] * 7
    since = (date.today() - timedelta(days=56)).isoformat()
    for d, c in db.execute("SELECT date, collected FROM stock_history WHERE date>=?", (since,)):
        by_weekday[date.fromisoformat(d).weekday()] += c
    best = by_weekday.index(max(by_weekday))
    day = date.today() + timedelta(days=1)
    while day.weekday() != best:
        day += timedelta(days=1)
    names = ["Mondays", "Tuesdays", "Wednesdays", "Thursdays", "Fridays", "Saturdays", "Sundays"]
    return {"blood_type": top["blood_type"], "city": city, "eligible_donors": n, "date": day.isoformat(),
            "best_day": names[best], "days_of_supply": top["days_of_supply"]}


@router.get("/reports")
def reports(user=Depends(only("organizer"))):
    with connect() as db:
        centre = dict(db.execute("SELECT * FROM centres WHERE id=?", (user.get("centre_id"),)).fetchone() or {})
        if not centre:
            raise HTTPException(422, "Your organizer account is not linked to a centre")
        appts = rows(db.execute("""SELECT a.status FROM appointments a JOIN slots s ON s.id=a.slot_id
                                   JOIN campaigns c ON c.id=s.campaign_id WHERE c.organizer_id=? AND c.event_date<?""",
                                (user["id"], today())))
        done = sum(a["status"] == "donated" for a in appts)
        no_show = sum(a["status"] == "no_show" for a in appts)
        fb = rows(db.execute("""SELECT f.rating,f.comment,f.created_at,c.title FROM feedback f JOIN campaigns c ON c.id=f.campaign_id
                                WHERE c.organizer_id=? ORDER BY f.created_at DESC, f.id DESC""", (user["id"],)))
        report, users = return_model(db)
        at_risk = []
        for s in report.scores:
            u = users[int(s.donor_id)]
            n = db.execute("SELECT COUNT(*) FROM donations WHERE donor_id=?", (u["id"],)).fetchone()[0]
            if n < 2 or s.p_return >= 0.4 or haversine_km(u["lat"], u["lng"], centre["lat"], centre["lng"]) > 25:
                continue
            at_risk.append({"name": u["name"], "blood_type": u["blood_type"], "donations": n, "days_since_last": s.days_since_last,
                            "p_return": round(s.p_return, 3), "top_factor": s.top_factor})
        at_risk.sort(key=lambda x: (-x["donations"], x["p_return"]))
        suggestion = campaign_suggestion(db, centre, most_urgent(outlook(db)))
    return {
        "centre": centre,
        "turnout": {"donated": done, "no_show": no_show, "total": done + no_show,
                    "no_show_rate": round(no_show / (done + no_show), 3) if done + no_show else 0},
        "ratings": {"average": round(sum(f["rating"] for f in fb) / len(fb), 2) if fb else None, "count": len(fb), "latest": fb[:5]},
        "at_risk": at_risk[:10],
        "model": report.report.model_dump(),
        "suggestion": suggestion,
    }


@router.get("/models")
def models(user=Depends(only("admin"))):
    from ai.evaluation import evaluate_all
    from forecast import MODEL_DIR, data_file
    with connect() as db:
        types = outlook(db)
        report, _ = return_model(db)
        profiles, health, _u = load_people(db)
        centres = load_centres(db)
    saved = None
    mfile = MODEL_DIR / "metrics.json"
    if mfile.exists():
        try:
            m = json.loads(mfile.read_text())
            fc = m.get("forecasts", [])
            saved = {"trained": m.get("trained"), "data_file": m.get("data_file"), "series": len(fc),
                     "chosen": {k: sum(1 for x in fc if x["selected"] == k) for k in ("rf", "weekday_mean", "seasonal_naive")},
                     "avg_gain": round(sum((x["baseline_mae"] - x["mae"]) / x["baseline_mae"] for x in fc if x["baseline_mae"])
                                       / max(1, sum(1 for x in fc if x["baseline_mae"])) * 100),
                     "national": [x for x in fc if x["region"] == "Malaysia"]}
        except (OSError, ValueError, KeyError, ZeroDivisionError):
            saved = None
    df = data_file()
    return {
        "evaluation": evaluate_all(profiles, health, centres),
        "training": saved,
        "official_data": {"present": bool(df), "file": df.name if df else None},
        "forecast": [{"blood_type": t["blood_type"], "collected": t["metrics"]["collected"], "used": t["metrics"]["used"]} for t in types],
        "return_model": report.report.model_dump(),
        "matching_weights": matching.WEIGHTS,
        "rules": eligibility.RULES,
        "llm": llm.status(),
        "note": DATA_NOTE,
    }


@router.post("/admin/llm/test")
def llm_test(user=Depends(only("admin"))):
    security.limit(f"llmtest:{user['id']}", 5, 60)
    return llm.test()


# ---------------------------------------------------------------- admin: user management


class RoleBody(BaseModel):
    role: Literal["donor", "organizer"]


@router.get("/admin/users")
def admin_users(q: str = "", role: str = "", user=Depends(only("admin"))):
    """Real (non-synthetic) accounts. Admins approve community organizers by changing a donor's role."""
    with connect() as db:
        counts = {r["role"]: r["n"] for r in db.execute(
            "SELECT role, COUNT(*) AS n FROM users WHERE is_synthetic=0 GROUP BY role").fetchall()}
        synthetic = db.execute("SELECT COUNT(*) FROM users WHERE is_synthetic=1").fetchone()[0]
        where, args = ["u.is_synthetic=0"], []
        if role in ("donor", "organizer", "admin"):
            where.append("u.role=?")
            args.append(role)
        if q.strip():
            where.append("(LOWER(u.name) LIKE ? OR LOWER(u.email) LIKE ?)")
            args += [f"%{q.strip().lower()}%"] * 2
        items = rows(db.execute(f"""SELECT u.id, u.name, u.email, u.role, u.blood_type, u.city, u.created_at,
                (SELECT COUNT(*) FROM donations d WHERE d.donor_id=u.id) AS donations,
                (SELECT COUNT(*) FROM campaigns c WHERE c.organizer_id=u.id) AS campaigns
                FROM users u WHERE {' AND '.join(where)} ORDER BY u.role='admin' DESC, u.role='organizer' DESC, u.id DESC LIMIT 100""",
                args))
    return {"counts": {"donor": counts.get("donor", 0), "organizer": counts.get("organizer", 0),
                       "admin": counts.get("admin", 0), "synthetic": synthetic}, "users": items}


@router.patch("/admin/users/{user_id}/role")
def admin_set_role(user_id: int, body: RoleBody, user=Depends(only("admin"))):
    with connect() as db:
        target = db.execute("SELECT id, role, is_synthetic FROM users WHERE id=?", (user_id,)).fetchone()
        if not target or target["is_synthetic"]:
            raise HTTPException(404, "User not found")
        if target["role"] == "admin":
            raise HTTPException(403, "Admin accounts can't be changed here")
        if target["role"] == body.role:
            return {"ok": True, "role": body.role}
        db.execute("UPDATE users SET role=? WHERE id=?", (body.role, user_id))
        up = body.role == "organizer"
        notifier.event(db, user_id, "role_change", status="approved" if up else "removed",
                       status_ms="diluluskan" if up else "ditarik balik",
                       message="You can now create donation campaigns and check donors in. Sign in again to see the "
                               "organizer menu." if up else "Your account is now a donor account.",
                       message_ms="Anda kini boleh mencipta kempen derma dan mendaftar masuk penderma. Log masuk semula "
                                  "untuk melihat menu penganjur." if up else "Akaun anda kini akaun penderma.")
        db.commit()
    return {"ok": True, "role": body.role}


# ---------------------------------------------------------------- assistant (used by app.py /api/assistant)


def assistant_answer(question: str, user: dict) -> dict:
    context, summary = "", None
    if user["role"] == "donor":
        with connect() as db:
            try:
                h = my_health(db, user)
                r = eligibility.evaluate(h, today())
                label = eligibility.VERDICT_LABEL[r.verdict]
                context = (f"\n\nContext about this donor (from the rules engine, do not change it): name {first_name(user['name'])}, "
                           f"blood type {h.blood_type}, {len(h.donations)} past donations, current status \"{label}\""
                           + (f", eligible from {r.eligible_from}" if r.eligible_from else "") + ".")
                summary = (f"Based on your record you can donate now — your last donation was {r.days_since_last} days ago."
                           if r.verdict == "eligible" and r.days_since_last is not None
                           else "Based on your record you can donate now." if r.verdict == "eligible"
                           else f"Based on your record you can donate again from {r.eligible_from}." if r.eligible_from
                           else "Your record needs a staff check before donating.")
            except HTTPException:
                summary = "Add your blood type, birth year and weight in My Profile so I can check your donation date."
    out = ai_assistant.reply(AssistantRequest(messages=[ChatMessage(role="user", content=question)],
                                              context=context, eligibility_summary=summary))
    mode = {"llm": "AI answer (LLM) · not medical advice", "faq": "curated FAQ (not generative medical advice)",
            "guardrail": "safety rule"}[out.source]
    return {"answer": out.reply, "mode": mode, "source": out.source}
