"""
HemoScan AI — private full blood count (FBC/CBC) report reader for donors.

Flow: upload PDF (or enter manually) → extracted draft → donor checks/edits and confirms →
rules engine analysis → AI (or template) explanation → saved in private history with trends.

Privacy: every endpoint is donor-only and owner-only (other users get 404). Files are stored with
random names outside the static folder and served with no-store caching. Deleting a report removes
the file and all its results.
"""
from __future__ import annotations

import csv
import html
import io
import json
import os
import secrets
from datetime import date, timedelta
from pathlib import Path
from typing import Literal, Optional

import pymupdf
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, HTMLResponse, Response
from pydantic import BaseModel, Field

from ai.hemoscan import interpret, rules
from ai.util import first_name
from ai.hemoscan import samples as sample_reports
from ai.hemoscan.biomarkers import BY_KEY, CATALOG, ORDER, UNIT_CHOICES, to_canonical
from ai.hemocare import knowledge
from ai.hemoscan import ocr
from ai.hemoscan.extract import ExtractionError, extract, extract_image
import security
from app import DB_PATH, connect, only, record_consent, rows, user_from_request

router = APIRouter(prefix="/api/hemoscan")
REPORT_DIR = Path(os.environ.get("HEMOLINK_REPORT_DIR", str(DB_PATH.parent / "hemoscan_reports")))
REPORT_DIR.mkdir(parents=True, exist_ok=True)
MAX_BYTES = 10 * 1024 * 1024
DISCLAIMER = ("HemoScan is an educational tool. It finds number patterns that are often linked with certain conditions — "
              "possible associations, not a diagnosis. Only a doctor can diagnose. If you feel unwell, seek medical care.")


# ---------------------------------------------------------------- helpers


def own_report(db, report_id: int, user: dict) -> dict:
    r = db.execute("SELECT * FROM hemo_reports WHERE id=? AND user_id=?", (report_id, user["id"])).fetchone()
    if not r:
        raise HTTPException(404, "Report not found")
    return dict(r)


def results_of(db, report_id: int) -> list[dict]:
    out = rows(db.execute("""SELECT biomarker AS key, value, unit, ref_low, ref_high, ref_source, flag, edited, confidence
                             FROM hemo_results WHERE report_id=?""", (report_id,)))
    return sorted(out, key=lambda x: ORDER.index(x["key"]) if x["key"] in ORDER else 99)


def previous_confirmed(db, user_id: int, before: str, exclude: int) -> tuple[list[dict] | None, str | None]:
    p = db.execute("""SELECT id, report_date FROM hemo_reports WHERE user_id=? AND status='confirmed' AND id<>?
                      AND report_date < ? ORDER BY report_date DESC, id DESC LIMIT 1""", (user_id, exclude, before)).fetchone()
    if not p:
        return None, None
    res = [{"key": x["key"], "value": x["value"], "unit": x["unit"],
            "ref_low": x["ref_low"] if x["ref_source"] == "lab" else None,
            "ref_high": x["ref_high"] if x["ref_source"] == "lab" else None} for x in results_of(db, p["id"])]
    return res, p["report_date"]


def confirm_report(db, report: dict, user: dict, report_date: str, sex: str, lab_name: str, results: list[dict]) -> dict:
    """Run the rules engine + explanation on confirmed values and save everything."""
    prev, prev_date = previous_confirmed(db, user["id"], report_date, report["id"])
    since = (date.fromisoformat(report_date) - timedelta(days=365)).isoformat()
    donations = db.execute("SELECT COUNT(*) FROM donations WHERE donor_id=? AND donated_on>=? AND donated_on<=?",
                           (user["id"], since, report_date)).fetchone()[0]
    analysis = rules.analyse(results, sex, prev, prev_date, donations_last_year=donations, is_donor=user["role"] == "donor")
    explanation, used_llm = interpret.explain(analysis, first_name(user["name"]))
    analysis["doctor_questions"] = interpret.doctor_questions(analysis)
    db.execute("DELETE FROM hemo_results WHERE report_id=?", (report["id"],))
    for x in analysis["results"]:
        db.execute("""INSERT INTO hemo_results(report_id,biomarker,value,unit,ref_low,ref_high,ref_source,flag,edited,confidence)
                      VALUES(?,?,?,?,?,?,?,?,?,?)""",
                   (report["id"], x["key"], x["value"], x["unit"], x["ref_low"], x["ref_high"], x["ref_source"], x["flag"],
                    int(bool(x.get("edited"))), x.get("confidence")))
    db.execute("""UPDATE hemo_reports SET status='confirmed', report_date=?, sex=?, lab_name=?, analysis=?, explanation=?,
                  used_llm=?, confirmed_at=CURRENT_TIMESTAMP WHERE id=?""",
               (report_date, sex, lab_name, json.dumps(analysis), explanation, int(used_llm), report["id"]))
    return analysis


def last_sex(db, user_id: int) -> str | None:
    r = db.execute("SELECT sex FROM hemo_reports WHERE user_id=? AND sex IS NOT NULL ORDER BY id DESC LIMIT 1", (user_id,)).fetchone()
    return r["sex"] if r else None


# ---------------------------------------------------------------- catalogue + samples


@router.get("/catalog")
def catalog(user=Depends(user_from_request)):
    return {
        "biomarkers": [{"key": b.key, "name": b.name, "unit": b.unit, "group": b.group, "explain": b.explain,
                        "percent": b.percent, "units": sorted({b.unit, *b.accepts, *(["/uL"] if b.unit.startswith("x10") else [])}),
                        "default_female": b.default_female, "default_male": b.default_male} for b in CATALOG],
        "unit_choices": UNIT_CHOICES,
        "rules": rules.rule_catalog(),
        "learn": {r["id"]: knowledge.for_rules([r["id"]])[:3] for r in rules.rule_catalog()},
        "references": list(rules.REFS.values()),
        "review": rules.REVIEW,
        "rules_version": rules.RULES_VERSION,
        "disclaimer": DISCLAIMER,
        "samples": [{"name": k, "label": v[0], "sub": v[1], "kind": v[2]} for k, v in sample_reports.SAMPLES.items()],
        "max_mb": MAX_BYTES // (1024 * 1024),
        "ocr": ocr.available(),
    }


@router.get("/samples/{name}")
def sample(name: str, user=Depends(user_from_request)):
    if name not in sample_reports.SAMPLES:
        raise HTTPException(404, "Sample not found")
    photo = name == "photo"
    return Response(sample_reports.make(name), media_type="image/jpeg" if photo else "application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="hemoscan-sample-{name}.{"jpg" if photo else "pdf"}"'})


# ---------------------------------------------------------------- create


def _save_report(user: dict, pdf: bytes, ext: dict, filename: str) -> dict:
    stored = secrets.token_hex(16) + ".pdf"
    security.write_encrypted(REPORT_DIR / stored, pdf)  # encrypted at rest
    with connect() as db:
        meta = ext["meta"]
        rid = db.execute(
            """INSERT INTO hemo_reports(user_id,source,original_name,stored_name,page_count,report_date,lab_name,sex,extraction)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (user["id"], "pdf", filename[:120], stored, len(ext["pages"]), meta["report_date"],
             meta["lab_name"] or "", meta["sex"] or last_sex(db, user["id"]), json.dumps(ext)),
        ).lastrowid
        record_consent(db, user["id"], "hemoscan_upload")
        db.commit()
    return {"id": rid, "needs_manual": ext["needs_manual"], "found": len(ext["items"]), "ocr": ext.get("ocr"),
            "photo": ext.get("photo", False)}


@router.post("/reports/upload")
async def upload(file: UploadFile = File(...), consent: bool = Form(False), user=Depends(only("donor"))):
    if not consent:
        raise HTTPException(422, "Please tick the box to confirm you understand HemoScan is not a diagnosis.")
    security.limit(f"upload:{user['id']}", 10, 600, "Upload limit reached — please wait a few minutes.")
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, f"File is larger than {MAX_BYTES // (1024 * 1024)} MB.")
    if not data.startswith(b"%PDF"):
        raise HTTPException(415, "Only PDF files are supported here. For a photo, use “Take a photo”.")
    try:
        ext = await run_in_threadpool(extract, data)  # OCR of scanned PDFs can take a few seconds
    except ExtractionError as exc:
        raise HTTPException(422, str(exc)) from exc
    return _save_report(user, data, ext, file.filename or "report.pdf")


@router.post("/reports/photo")
async def upload_photo(file: UploadFile = File(...), consent: bool = Form(False), user=Depends(only("donor"))):
    """Camera / gallery photo of a paper report → stored as a one-page PDF → OCR pre-fill → user checks every value."""
    if not consent:
        raise HTTPException(422, "Please tick the box to confirm you understand HemoScan is not a diagnosis.")
    security.limit(f"upload:{user['id']}", 10, 600, "Upload limit reached — please wait a few minutes.")
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, f"Photo is larger than {MAX_BYTES // (1024 * 1024)} MB.")
    try:
        pdf, ext = await run_in_threadpool(extract_image, data, file.content_type or "")
    except ExtractionError as exc:
        raise HTTPException(422, str(exc)) from exc
    return _save_report(user, pdf, ext, f"photo-{date.today().isoformat()}.pdf")


class ManualBody(BaseModel):
    report_date: Optional[date] = None
    lab_name: str = Field(default="", max_length=120)


@router.post("/reports/manual")
def manual(body: ManualBody, user=Depends(only("donor"))):
    ext = {"scanned": False, "needs_manual": True, "manual": True, "pages": [], "items": [], "missing": [],
           "meta": {}, "warnings": []}
    with connect() as db:
        rid = db.execute("""INSERT INTO hemo_reports(user_id,source,report_date,lab_name,sex,extraction)
                            VALUES(?,?,?,?,?,?)""",
                         (user["id"], "manual", (body.report_date or date.today()).isoformat(), body.lab_name.strip(),
                          last_sex(db, user["id"]), json.dumps(ext))).lastrowid
        db.commit()
    return {"id": rid}


# ---------------------------------------------------------------- read


@router.get("/reports")
def list_reports(user=Depends(only("donor"))):
    with connect() as db:
        items = rows(db.execute("""SELECT id,source,original_name,report_date,lab_name,status,analysis,created_at,
                                   json_extract(extraction,'$.photo') AS photo
                                   FROM hemo_reports WHERE user_id=? ORDER BY COALESCE(report_date, created_at) DESC, id DESC""",
                                (user["id"],)))
    out = []
    for r in items:
        a = json.loads(r.pop("analysis") or "null")
        r["counts"] = a["counts"] if a else None
        r["urgent"] = bool(a and a["urgent"])
        r["top_finding"] = a["findings"][0]["title"] if a and a["findings"] else None
        out.append(r)
    return out


@router.get("/reports/{report_id}")
def get_report(report_id: int, user=Depends(only("donor"))):
    with connect() as db:
        r = own_report(db, report_id, user)
        res = results_of(db, report_id) if r["status"] == "confirmed" else []
    ext = json.loads(r.pop("extraction") or "{}")
    analysis = json.loads(r.pop("analysis") or "null")
    r.pop("stored_name", None)
    return {"report": {**r, "has_file": r["source"] == "pdf"}, "extraction": ext, "results": res, "analysis": analysis,
            "disclaimer": DISCLAIMER}


@router.get("/reports/{report_id}/file")
def report_file(report_id: int, user=Depends(only("donor"))):
    with connect() as db:
        r = own_report(db, report_id, user)
    path = REPORT_DIR / (r["stored_name"] or "")
    if not r["stored_name"] or not path.is_file():
        raise HTTPException(404, "No PDF stored for this report")
    name = (r["original_name"] or "report.pdf").replace('"', "")
    return Response(security.read_decrypted(path), media_type="application/pdf",
                    headers={"Cache-Control": "private, no-store", "Content-Disposition": f'inline; filename="{name}"'})


@router.get("/reports/{report_id}/page/{page_no}")
def report_page(report_id: int, page_no: int, user=Depends(only("donor"))):
    with connect() as db:
        r = own_report(db, report_id, user)
    path = REPORT_DIR / (r["stored_name"] or "")
    if not r["stored_name"] or not path.is_file():
        raise HTTPException(404, "No PDF stored for this report")
    doc = pymupdf.open(stream=security.read_decrypted(path), filetype="pdf")
    try:
        if not 0 <= page_no < doc.page_count:
            raise HTTPException(404, "Page not found")
        page = doc[page_no]
        zoom = min(110 / 72, 1100 / max(page.rect.width, 1))  # photos become large pages; keep the preview light
        png = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).tobytes("png")
    finally:
        doc.close()
    return Response(png, media_type="image/png", headers={"Cache-Control": "private, no-store"})


@router.get("/history")
def history(user=Depends(only("donor"))):
    with connect() as db:
        reps = rows(db.execute("""SELECT id, report_date, lab_name FROM hemo_reports WHERE user_id=? AND status='confirmed'
                                  ORDER BY report_date, id""", (user["id"],)))
        series: dict[str, list] = {}
        for rep in reps:
            for x in results_of(db, rep["id"]):
                series.setdefault(x["key"], []).append({"report_id": rep["id"], "date": rep["report_date"], "value": x["value"],
                                                        "flag": x["flag"], "ref_low": x["ref_low"], "ref_high": x["ref_high"]})
    return {"reports": reps, "series": series,
            "biomarkers": [{"key": k, "name": BY_KEY[k].name, "unit": BY_KEY[k].unit} for k in ORDER if k in series]}


# ---------------------------------------------------------------- confirm / edit / delete


class ResultIn(BaseModel):
    key: str
    value: Optional[float] = None
    unit: Optional[str] = None
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None
    edited: bool = False
    confidence: Optional[float] = None


class ConfirmBody(BaseModel):
    report_date: date
    sex: Literal["female", "male"]
    lab_name: str = Field(default="", max_length=120)
    checked: bool = False
    results: list[ResultIn]


@router.post("/reports/{report_id}/confirm")
def confirm(report_id: int, body: ConfirmBody, user=Depends(only("donor"))):
    if not body.checked:
        raise HTTPException(422, "Please confirm you have checked the values against your report.")
    if body.report_date > date.today():
        raise HTTPException(422, "The report date can't be in the future.")
    clean, seen = [], set()
    for x in body.results:
        if x.value is None:
            continue
        if x.key not in BY_KEY or x.key in seen:
            raise HTTPException(422, f"Unknown or duplicate test: {x.key}")
        seen.add(x.key)
        b = BY_KEY[x.key]
        if not x.unit:
            raise HTTPException(422, f"Please choose a unit for {b.name}.")
        value, problem = to_canonical(x.key, x.value, x.unit)
        if problem:
            raise HTTPException(422, f"{b.name}: {problem}. Use {b.unit}" + (f" or {', '.join(b.accepts)}" if b.accepts else "") + ".")
        lo = to_canonical(x.key, x.ref_low, x.unit)[0] if x.ref_low is not None else None
        hi = to_canonical(x.key, x.ref_high, x.unit)[0] if x.ref_high is not None else None
        if lo is not None and hi is not None and lo > hi:
            raise HTTPException(422, f"{b.name}: the reference range low value is higher than the high value.")
        pl, ph = b.plausible
        if not pl <= value <= ph:
            raise HTTPException(422, f"{b.name}: {value:g} {b.unit} is outside what is physically possible — please check the value and unit.")
        clean.append({"key": x.key, "value": round(value, 3), "unit": b.unit, "ref_low": lo, "ref_high": hi,
                      "edited": x.edited, "confidence": x.confidence})
    if not any(not BY_KEY[c["key"]].percent for c in clean):
        raise HTTPException(422, "Please enter at least one test value.")
    with connect() as db:
        r = own_report(db, report_id, user)
        analysis = confirm_report(db, r, user, body.report_date.isoformat(), body.sex, body.lab_name.strip(), clean)
        db.commit()
    return {"ok": True, "findings": len(analysis["findings"]), "urgent": bool(analysis["urgent"])}


@router.post("/reports/{report_id}/reopen")
def reopen(report_id: int, user=Depends(only("donor"))):
    """Back to draft for editing; the confirmed values become the editable draft."""
    with connect() as db:
        r = own_report(db, report_id, user)
        ext = json.loads(r["extraction"] or "{}")
        old = {i["key"]: i for i in ext.get("items", [])}
        items = []
        for x in results_of(db, report_id):
            src = old.get(x["key"], {})
            items.append({**src, "key": x["key"], "name": BY_KEY[x["key"]].name, "value": x["value"], "unit": x["unit"],
                          "ref_low": x["ref_low"] if x["ref_source"] == "lab" else None,
                          "ref_high": x["ref_high"] if x["ref_source"] == "lab" else None,
                          "confidence_level": src.get("confidence_level", "high"), "problems": [], "edited": bool(x["edited"])})
        ext["items"] = items
        db.execute("DELETE FROM hemo_results WHERE report_id=?", (report_id,))
        db.execute("UPDATE hemo_reports SET status='draft', analysis=NULL, explanation=NULL, extraction=? WHERE id=?",
                   (json.dumps(ext), report_id))
        db.commit()
    return {"ok": True}


@router.delete("/reports/{report_id}")
def delete(report_id: int, user=Depends(only("donor"))):
    with connect() as db:
        r = own_report(db, report_id, user)
        db.execute("DELETE FROM hemo_results WHERE report_id=?", (report_id,))
        db.execute("DELETE FROM hemo_reports WHERE id=?", (report_id,))
        db.commit()
    if r["stored_name"]:
        (REPORT_DIR / r["stored_name"]).unlink(missing_ok=True)
    return {"ok": True}


# ---------------------------------------------------------------- assistant


class AskBody(BaseModel):
    question: str = Field(min_length=2, max_length=500)


@router.post("/reports/{report_id}/ask")
def ask(report_id: int, body: AskBody, user=Depends(only("donor"))):
    security.limit(f"ai:{user['id']}", 20, 60, "You're asking very fast — please wait a minute.")
    with connect() as db:
        r = own_report(db, report_id, user)
    if r["status"] != "confirmed":
        raise HTTPException(409, "Confirm the values first, then ask questions about the report.")
    return interpret.answer(body.question, json.loads(r["analysis"]))


# ---------------------------------------------------------------- export


@router.get("/export.csv")
def export_csv(user=Depends(only("donor"))):
    with connect() as db:
        data = rows(db.execute("""SELECT r.report_date, r.lab_name, x.biomarker, x.value, x.unit, x.ref_low, x.ref_high,
                                  x.ref_source, x.flag FROM hemo_results x JOIN hemo_reports r ON r.id=x.report_id
                                  WHERE r.user_id=? AND r.status='confirmed' ORDER BY r.report_date, x.id""", (user["id"],)))
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["report_date", "lab", "test", "value", "unit", "ref_low", "ref_high", "range_source", "flag"])
    for d in data:
        w.writerow([d["report_date"], d["lab_name"], BY_KEY[d["biomarker"]].name, d["value"], d["unit"], d["ref_low"],
                    d["ref_high"], d["ref_source"], d["flag"]])
    return Response(buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="hemoscan-history.csv"', "Cache-Control": "no-store"})


@router.get("/reports/{report_id}/summary", response_class=HTMLResponse)
def summary(report_id: int, user=Depends(only("donor"))):
    """Printable one-page summary to take to a doctor (use the browser's Print → Save as PDF)."""
    with connect() as db:
        r = own_report(db, report_id, user)
    if r["status"] != "confirmed":
        raise HTTPException(409, "Confirm the values first.")
    a = json.loads(r["analysis"])
    h = html.escape
    res_rows = "".join(
        f"<tr class='{x['flag']}'><td>{h(x['name'])}</td><td><b>{x['value']:g}</b></td><td>{h(x['unit'])}</td>"
        f"<td>{x['ref_low']:g} – {x['ref_high']:g}{'' if x['ref_source'] == 'lab' else ' *'}</td><td>{h(x['flag'])}</td></tr>"
        for x in a["results"])
    finds = "".join(
        f"<div class='f'><b>{h(f['title'])}</b> <span class='sev'>{h(f['severity_label'])}</span>"
        f"<div>Triggered by: {h('; '.join(f['why']))}</div>"
        + (f"<div>{h(f['detail'])}</div>" if f.get("detail") else "")
        + f"<div>Possible associations: {h(', '.join(f['associations']))}</div>"
          f"<div>Usual next steps: {h(', '.join(f['next_steps']))}</div></div>" for f in a["findings"]) \
        or "<p>No pattern rules were triggered.</p>"
    trend_rows = "".join(
        f"<tr><td>{h(t['name'])}</td><td>{t['previous']:g}</td><td>{t['current']:g}</td><td>{t['change']:+g} {h(t['unit'])}</td>"
        f"<td>{h(t['note'] or '')}</td></tr>" for t in a["trends"])
    qs = "".join(f"<li>{h(q)}</li>" for q in a.get("doctor_questions", []))
    don = a.get("donation")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>HemoScan summary {h(r['report_date'] or '')}</title>
<style>body{{font:13px/1.5 Arial,sans-serif;color:#222;max-width:820px;margin:24px auto;padding:0 16px}}h1{{font-size:20px;margin:0}}
h2{{font-size:15px;margin:22px 0 6px;border-bottom:1px solid #ddd;padding-bottom:4px}}table{{border-collapse:collapse;width:100%}}
td,th{{border-bottom:1px solid #eee;padding:5px 6px;text-align:left}}tr.low td,tr.high td{{background:#fff4e5}}
.f{{border:1px solid #e5e5e5;border-radius:6px;padding:8px 10px;margin:6px 0}}.sev{{font-size:11px;color:#a33;margin-left:6px}}
.note{{background:#f6f6f6;padding:8px 10px;border-radius:6px}}.urgent{{background:#fde8e8;border:1px solid #f3b5b5;padding:10px;border-radius:6px}}
@media print{{button{{display:none}}}}</style></head><body>
<button data-print style="float:right">Print / Save as PDF</button><script src="/static/print.js"></script>
<h1>HemoScan summary — for discussion with a healthcare professional</h1>
<p>{h(user['name'])} · Report date {h(r['report_date'] or '-')} · {h(r['lab_name'] or 'Lab not stated')} · Sex used for ranges: {h(r['sex'] or '-')}</p>
{"<div class='urgent'><b>Possibly urgent values:</b> " + h('; '.join(u['rule'] for u in a['urgent'])) + ". " + h(rules.URGENT_ADVICE) + "</div>" if a['urgent'] else ""}
<h2>Results (values confirmed by the user)</h2><table><tr><th>Test</th><th>Value</th><th>Unit</th><th>Reference</th><th>Flag</th></tr>{res_rows}</table>
<p style="font-size:11px">* Typical adult range used because the report had none.</p>
<h2>Patterns found by the rules engine</h2>{finds}
{"<h2>Changes since previous report</h2><table><tr><th>Test</th><th>Before</th><th>Now</th><th>Change</th><th></th></tr>" + trend_rows + "</table>" if trend_rows else ""}
{"<h2>Blood donation</h2><p>" + h(don['message']) + (" " + h(don['frequent_donor_note']) if don.get('frequent_donor_note') else "") + "</p>" if don else ""}
<h2>Questions to ask</h2><ul>{qs}</ul>
<h2>Limitations</h2><div class="note">{"<br>".join(h(x) for x in a["limitations"])}</div>
<p style="font-size:11px;color:#666">Generated by HemoLink AI · HemoScan rules {h(a['rules_version'])} ({h(a['review']['status'])}) on {date.today().isoformat()}.
{h(DISCLAIMER)}</p></body></html>"""
    return HTMLResponse(page, headers={"Cache-Control": "private, no-store"})


# ---------------------------------------------------------------- demo history for the demo donor


def seed_demo_history() -> None:
    """Two earlier confirmed reports for donor@demo.com so the trend chart has history."""
    with connect() as db:
        u = db.execute("SELECT id,name,role FROM users WHERE email='donor@demo.com'").fetchone()
        if not u or db.execute("SELECT 1 FROM hemo_reports WHERE user_id=?", (u["id"],)).fetchone():
            return
        user = dict(u)
        for name in ("history1", "history2"):
            data = sample_reports.make(name)
            ext = extract(data)
            stored = secrets.token_hex(16) + ".pdf"
            security.write_encrypted(REPORT_DIR / stored, data)
            meta = ext["meta"]
            rid = db.execute("""INSERT INTO hemo_reports(user_id,source,original_name,stored_name,page_count,report_date,
                                lab_name,sex,extraction) VALUES(?,?,?,?,?,?,?,?,?)""",
                             (user["id"], "pdf", f"fbc-{meta['report_date']}.pdf", stored, len(ext["pages"]),
                              meta["report_date"], meta["lab_name"], meta["sex"], json.dumps(ext))).lastrowid
            report = dict(db.execute("SELECT * FROM hemo_reports WHERE id=?", (rid,)).fetchone())
            items = [{k: i[k] for k in ("key", "value", "unit", "ref_low", "ref_high")} for i in ext["items"]]
            confirm_report(db, report, user, meta["report_date"], meta["sex"], meta["lab_name"], items)
        db.commit()


seed_demo_history()
