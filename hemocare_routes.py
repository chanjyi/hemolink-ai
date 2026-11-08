"""
HemoCare — the donor's personal blood health hub.

  * Medical Knowledge: plain-language guides (anaemia, iron, thalassaemia, platelets, dengue …), linked from
    HemoScan findings. Educational only — no doses, no diagnosis.
  * Medication History: the donor's own private medicine list, checked against example donation waiting periods.
    A waiting period feeds the Eligibility Check and keeps the donor out of urgent-alert matching until it ends.
  * Donation preparation: one printable summary to bring to the screening interview.
Donor-only, owner-only — organizers and admins can't see any of it.
"""
from __future__ import annotations

import html
import json
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, field_validator

from ai import eligibility
from ai.hemocare import knowledge, meds
from ai_routes import hemoscan_hint, my_health
from app import connect, only, rows

router = APIRouter(prefix="/api/hemocare")
DISCLAIMER = ("HemoCare is educational. It does not diagnose or recommend treatment — follow your doctor's and "
              "pharmacist's advice, and never stop a prescribed medicine just to donate.")


# ---------------------------------------------------------------- helpers


def my_meds(db, user_id: int) -> list[dict]:
    items = rows(db.execute("""SELECT id, name, category, reason, dose_note, start_date, end_date, notes, created_at
                               FROM hemo_meds WHERE user_id=? ORDER BY (end_date IS NULL) DESC, COALESCE(end_date, '9999') DESC,
                               id DESC""", (user_id,)))
    for m in items:
        m["status"] = meds.status(m)
    return items


def latest_insights(db, user_id: int) -> dict | None:
    r = db.execute("""SELECT id, report_date, analysis FROM hemo_reports WHERE user_id=? AND status='confirmed'
                      ORDER BY report_date DESC, id DESC LIMIT 1""", (user_id,)).fetchone()
    if not r:
        return None
    a = json.loads(r["analysis"] or "{}")
    findings = [f for f in a.get("findings", []) if f["id"] != "urgent_values"]
    return {"report_id": r["id"], "report_date": r["report_date"], "urgent": bool(a.get("urgent")),
            "findings": [{"id": f["id"], "title": f["title"], "severity_label": f["severity_label"]} for f in findings],
            "articles": knowledge.for_rules([f["id"] for f in findings])}


def eligibility_status(db, user: dict) -> dict | None:
    try:
        h = my_health(db, user)
    except HTTPException:
        return None
    r = eligibility.evaluate(h, date.today().isoformat())
    return {**r.model_dump(), "label": eligibility.VERDICT_LABEL[r.verdict]}


# ---------------------------------------------------------------- knowledge


@router.get("/overview")
def overview(user=Depends(only("donor"))):
    with connect() as db:
        ms = my_meds(db, user["id"])
        insight = latest_insights(db, user["id"])
    current = [m for m in ms if m["status"]["ongoing"]]
    return {"articles": knowledge.summary_list(), "insights": insight,
            "meds": {"total": len(ms), "current": len(current), "hold": meds.hold(ms)},
            "review": knowledge.REVIEW, "disclaimer": DISCLAIMER}


@router.get("/articles/{article_id}")
def get_article(article_id: str, user=Depends(only("donor"))):
    a = knowledge.article(article_id)
    if not a:
        raise HTTPException(404, "Article not found")
    with connect() as db:
        insight = latest_insights(db, user["id"])
    mine = []
    if insight:  # show which of the donor's own HemoScan findings this guide relates to
        mine = [f for f in insight["findings"] if f["id"] in a["rules"]]
    return {**a, "my_findings": mine, "my_report": insight and {"id": insight["report_id"], "date": insight["report_date"]},
            "disclaimer": DISCLAIMER}


# ---------------------------------------------------------------- medication history


class MedBody(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    category: str = "auto"
    reason: str = Field(default="", max_length=120)
    dose_note: str = Field(default="", max_length=80)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: str = Field(default="", max_length=300)

    @field_validator("category")
    @classmethod
    def known_category(cls, v: str) -> str:
        if v != "auto" and v not in meds.CATEGORIES:
            raise ValueError("Unknown medicine type")
        return v


def _check_dates(body: MedBody) -> None:
    if body.start_date and body.start_date > date.today() + timedelta(days=1):
        raise HTTPException(422, "The start date can't be in the future.")
    if body.start_date and body.end_date and body.end_date < body.start_date:
        raise HTTPException(422, "The last dose can't be before the start date.")


def _values(body: MedBody) -> tuple:
    category = meds.detect(body.name) if body.category == "auto" else body.category
    return (body.name.strip(), category, body.reason.strip(), body.dose_note.strip(),
            body.start_date.isoformat() if body.start_date else None,
            body.end_date.isoformat() if body.end_date else None, body.notes.strip())


@router.get("/meds")
def list_meds(user=Depends(only("donor"))):
    with connect() as db:
        ms = my_meds(db, user["id"])
    return {"items": ms, "hold": meds.hold(ms), "categories": meds.CATEGORY_CHOICES, "note": meds.PLACEHOLDER,
            "disclaimer": DISCLAIMER}


@router.post("/meds")
def add_med(body: MedBody, user=Depends(only("donor"))):
    _check_dates(body)
    with connect() as db:
        if db.execute("SELECT COUNT(*) FROM hemo_meds WHERE user_id=?", (user["id"],)).fetchone()[0] >= 200:
            raise HTTPException(422, "Your medicine list is full (200 entries).")
        mid = db.execute("""INSERT INTO hemo_meds(user_id,name,category,reason,dose_note,start_date,end_date,notes)
                            VALUES(?,?,?,?,?,?,?,?)""", (user["id"], *_values(body))).lastrowid
        db.commit()
    return {"id": mid, "status": meds.status({"name": body.name, "category": _values(body)[1],
                                              "end_date": body.end_date.isoformat() if body.end_date else None})}


def _own_med(db, med_id: int, user: dict):
    if not db.execute("SELECT 1 FROM hemo_meds WHERE id=? AND user_id=?", (med_id, user["id"])).fetchone():
        raise HTTPException(404, "Medicine not found")


@router.put("/meds/{med_id}")
def update_med(med_id: int, body: MedBody, user=Depends(only("donor"))):
    _check_dates(body)
    with connect() as db:
        _own_med(db, med_id, user)
        db.execute("""UPDATE hemo_meds SET name=?,category=?,reason=?,dose_note=?,start_date=?,end_date=?,notes=?
                      WHERE id=?""", (*_values(body), med_id))
        db.commit()
    return {"ok": True}


class StopBody(BaseModel):
    end_date: date


@router.post("/meds/{med_id}/stop")
def stop_med(med_id: int, body: StopBody, user=Depends(only("donor"))):
    with connect() as db:
        _own_med(db, med_id, user)
        start = db.execute("SELECT start_date FROM hemo_meds WHERE id=?", (med_id,)).fetchone()["start_date"]
        if start and body.end_date.isoformat() < start:
            raise HTTPException(422, "The last dose can't be before the start date.")
        db.execute("UPDATE hemo_meds SET end_date=? WHERE id=?", (body.end_date.isoformat(), med_id))
        db.commit()
    return {"ok": True}


@router.delete("/meds/{med_id}")
def delete_med(med_id: int, user=Depends(only("donor"))):
    with connect() as db:
        _own_med(db, med_id, user)
        db.execute("DELETE FROM hemo_meds WHERE id=?", (med_id,))
        db.commit()
    return {"ok": True}


# ---------------------------------------------------------------- donation preparation


def prep_data(db, user: dict) -> dict:
    ms = my_meds(db, user["id"])
    recent_cut = (date.today() - timedelta(days=90)).isoformat()
    mention = [m for m in ms if m["status"]["ongoing"] or (m["end_date"] and m["end_date"] >= recent_cut)]
    return {
        "eligibility": eligibility_status(db, user),
        "hemoscan": hemoscan_hint(db, user["id"]),
        "insights": latest_insights(db, user["id"]),
        "medicines": mention,
        "hold": meds.hold(ms),
        "checklist": ["Sleep well the night before", "Eat a proper meal and drink 2–3 glasses of water",
                      "Bring your IC or passport", "Avoid coffee and cigarettes for a few hours before",
                      "Bring this summary or your medicine list to the screening interview"],
    }


@router.get("/prep")
def prep(user=Depends(only("donor"))):
    with connect() as db:
        return {**prep_data(db, user), "disclaimer": DISCLAIMER}


@router.get("/prep/summary", response_class=HTMLResponse)
def prep_summary(user=Depends(only("donor"))):
    """Printable page for the screening interview (browser Print → Save as PDF)."""
    with connect() as db:
        d = prep_data(db, user)
    h = html.escape
    el = d["eligibility"]
    el_txt = (f"{h(el['label'])}" + (f" — from {h(el['eligible_from'])}" if el.get("eligible_from") and el["verdict"] == "deferred"
                                     else "") if el else "Profile incomplete (blood type, birth year, weight)")
    med_rows = "".join(
        f"<tr><td><b>{h(m['name'])}</b>{'<br><small>' + h(m['dose_note']) + '</small>' if m['dose_note'] else ''}</td>"
        f"<td>{h(m['reason'] or '-')}</td><td>{h(m['start_date'] or '-')}</td>"
        f"<td>{'Still taking' if m['status']['ongoing'] and not m['end_date'] else h(m['end_date'] or '-')}</td>"
        f"<td>{h(m['status']['message'])}</td></tr>" for m in d["medicines"]) or "<tr><td colspan=5>No medicines recorded in the last 90 days.</td></tr>"
    hb = d["hemoscan"]
    ins = d["insights"]
    finds = ", ".join(f["title"] for f in ins["findings"]) if ins and ins["findings"] else "No patterns flagged"
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Donation screening summary</title>
<style>body{{font:13px/1.55 Arial,sans-serif;color:#222;max-width:820px;margin:24px auto;padding:0 16px}}h1{{font-size:20px;margin:0}}
h2{{font-size:15px;margin:22px 0 6px;border-bottom:1px solid #ddd;padding-bottom:4px}}table{{border-collapse:collapse;width:100%}}
td,th{{border-bottom:1px solid #eee;padding:6px;text-align:left;vertical-align:top}}.box{{background:#f6f6f6;padding:10px 12px;border-radius:6px}}
.hold{{background:#fff4e5;border:1px solid #f1d9b3;padding:10px 12px;border-radius:6px;margin-top:8px}}@media print{{button{{display:none}}}}</style></head><body>
<button data-print style="float:right">Print / Save as PDF</button><script src="/static/print.js"></script>
<h1>Donation screening summary</h1>
<p>{h(user['name'])} · Blood type {h(user.get('blood_type') or '-')} · Prepared {date.today().isoformat()} with HemoLink HemoCare</p>
<h2>Eligibility (HemoLink check)</h2><div class="box">{el_txt}</div>
{"<div class='hold'><b>Medicine waiting period:</b> " + h(d['hold']['reason']) + "</div>" if d['hold'] else ""}
<h2>Latest blood test (HemoScan, values confirmed by the donor)</h2>
<div class="box">{h(hb['message']) if hb else "No confirmed HemoScan report."}<br>Patterns: {h(finds)}</div>
<h2>Medicines — current and last 90 days</h2>
<table><tr><th>Medicine</th><th>For</th><th>Started</th><th>Last dose</th><th>Donation note (placeholder)</th></tr>{med_rows}</table>
<h2>Before you donate</h2><ul>{"".join(f"<li>{h(x)}</li>" for x in d['checklist'])}</ul>
<p style="font-size:11px;color:#666">Self-reported by the donor; not medically verified. Waiting periods are examples pending confirmation with
Pusat Darah Negara — screening staff make the final decision. {h(DISCLAIMER)}</p></body></html>"""
    return HTMLResponse(page, headers={"Cache-Control": "private, no-store"})
