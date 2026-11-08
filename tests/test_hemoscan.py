"""Tests for HemoScan AI (extraction, rules, privacy, API); run: python -m pytest -q"""
import os
import tempfile
from pathlib import Path

if "HEMOLINK_DB_PATH" not in os.environ:
    os.environ["HEMOLINK_DB_PATH"] = str(Path(tempfile.mkdtemp()) / "tests.db")

from fastapi.testclient import TestClient

from ai.hemoscan import interpret, rules, samples
from ai.hemoscan.biomarkers import to_canonical
from ai.hemoscan.extract import extract, parse_line
from app import app

H = {"X-HemoLink-Request": "app"}


def client(email="donor@demo.com", password="Demo123!"):
    c = TestClient(app)
    r = c.post("/api/login", json={"email": email, "password": password}, headers=H)
    assert r.status_code == 200, r.text
    return c


def upload(c, name="latest"):
    r = c.post("/api/hemoscan/reports/upload", files={"file": (f"{name}.pdf", samples.make(name), "application/pdf")},
               data={"consent": "true"}, headers=H)
    assert r.status_code == 200, r.text
    return r.json()


def confirm_body(detail, **over):
    ex = detail["extraction"]
    body = {"report_date": detail["report"]["report_date"], "sex": "female", "lab_name": "Demo", "checked": True,
            "results": [{k: i[k] for k in ("key", "value", "unit", "ref_low", "ref_high")} for i in ex["items"]]}
    body.update(over)
    return body


# ---------------- extraction ----------------


def test_extracts_table_report_with_units_ranges_and_meta():
    ex = extract(samples.make("latest"))
    items = {i["key"]: i for i in ex["items"]}
    assert not ex["scanned"] and not ex["missing"]
    assert items["hgb"]["value"] == 11.2 and items["hgb"]["unit"] == "g/dL"
    assert (items["hgb"]["ref_low"], items["hgb"]["ref_high"]) == (12.0, 15.5)
    assert items["mcv"]["lab_flag"] == "low" and items["plt"]["lab_flag"] == "high"
    assert items["hgb"]["bbox"] and items["hgb"]["confidence_level"] == "high"
    assert ex["meta"]["sex"] == "female" and ex["meta"]["report_date"]


def test_si_units_are_converted():
    ex = extract(samples.make("dengue"))
    items = {i["key"]: i for i in ex["items"]}
    assert items["hgb"]["value"] == 13.8 and items["hgb"]["ref_low"] == 12.0      # g/L -> g/dL
    assert items["hct"]["value"] == 44.0                                           # L/L -> %
    assert items["plt"]["value"] == 58 and items["wbc"]["value"] == 2.6            # x10^3/uL == x10^9/L
    assert "neut_pct" in items and "neut" not in items                             # % differential kept apart


def test_scanned_pdf_is_ocr_prefilled_but_never_trusted():
    from ai.hemoscan import ocr
    ex = extract(samples.make("scanned"))
    assert ex["scanned"]
    if ocr.available():  # values pre-filled, but none marked high confidence and every one flagged for checking
        assert ex["items"] and ex["ocr"]
        assert all(i["confidence_level"] in ("medium", "low") for i in ex["items"])
        assert all(i.get("ocr") for i in ex["items"])
    else:  # no OCR engine: manual entry, nothing guessed
        assert ex["needs_manual"] and ex["items"] == []


def test_photo_upload_reads_values_for_checking():
    from ai.hemoscan import ocr
    c = client()
    r = c.post("/api/hemoscan/reports/photo", files={"file": ("p.jpg", samples.make("photo"), "image/jpeg")},
               data={"consent": "true"}, headers=H)
    assert r.status_code == 200, r.text
    d = c.get(f"/api/hemoscan/reports/{r.json()['id']}").json()
    assert d["extraction"]["photo"] and d["report"]["has_file"]
    if ocr.available():
        items = {i["key"]: i for i in d["extraction"]["items"]}
        assert items["hgb"]["value"] == 11.2 and items["plt"]["value"] == 412
        assert all(i["confidence_level"] != "high" for i in items.values())
    assert c.get(f"/api/hemoscan/reports/{r.json()['id']}/page/0").headers["content-type"] == "image/png"
    bad = c.post("/api/hemoscan/reports/photo", files={"file": ("p.gif", b"GIF89a", "image/gif")}, data={"consent": "true"},
                 headers=H)
    assert bad.status_code == 422
    c.delete(f"/api/hemoscan/reports/{r.json()['id']}", headers=H)


def test_missing_unit_is_flagged_low_confidence():
    from ai.hemoscan.extract import score
    item = score(parse_line("Haemoglobin 11.2 12.0 - 15.5"))
    assert item["confidence_level"] != "high"
    assert any("Unit missing" in p for p in item["problems"])
    assert to_canonical("hgb", 112, "g/L")[0] == 11.2


# ---------------- rules ----------------


def r(key, value, unit, lo=None, hi=None):
    return {"key": key, "value": value, "unit": unit, "ref_low": lo, "ref_high": hi}


def test_low_hb_low_mcv_triggers_microcytic_pattern_with_explanation():
    a = rules.analyse([r("hgb", 10.5, "g/dL", 12, 15.5), r("mcv", 72, "fL", 80, 100), r("rbc", 5.4, "x10^12/L", 4, 5.2)],
                      "female")
    ids = [f["id"] for f in a["findings"]]
    assert "microcytic_anaemia" in ids and "mentzer" in ids
    f = next(f for f in a["findings"] if f["id"] == "microcytic_anaemia")
    assert f["why"] and f["references"] and f["associations"]
    assert a["review"]["status"].startswith("Pending")


def test_urgent_values_come_first():
    a = rules.analyse([r("hgb", 6.1, "g/dL"), r("plt", 30, "x10^9/L")], "male")
    assert a["urgent"] and a["findings"][0]["id"] == "urgent_values"


def test_normal_report_has_no_findings_and_typical_range_is_labelled():
    a = rules.analyse([r("hgb", 14, "g/dL"), r("wbc", 6, "x10^9/L")], "male")
    assert a["findings"] == [] and all(x["ref_source"] == "typical adult range" for x in a["results"])


def test_assistant_refuses_diagnosis_and_treatment():
    a = rules.analyse([r("hgb", 10.5, "g/dL", 12, 15.5), r("mcv", 72, "fL", 80, 100)], "female")
    assert interpret.answer("Do I have thalassaemia?", a)["source"] == "guardrail"
    assert interpret.answer("How much iron tablet should I take?", a)["source"] == "guardrail"
    text = interpret.template_explanation(a, "Amira")
    assert "not a diagnosis" in text


# ---------------- API ----------------


def test_upload_confirm_analyse_trend_and_export():
    c = client()
    rid = upload(c)["id"]
    d = c.get(f"/api/hemoscan/reports/{rid}").json()
    assert d["report"]["status"] == "draft" and d["analysis"] is None
    assert c.post(f"/api/hemoscan/reports/{rid}/confirm", json=confirm_body(d, checked=False), headers=H).status_code == 422
    assert c.post(f"/api/hemoscan/reports/{rid}/confirm", json=confirm_body(d), headers=H).status_code == 200
    d = c.get(f"/api/hemoscan/reports/{rid}").json()
    assert "microcytic_anaemia" in [f["id"] for f in d["analysis"]["findings"]]
    assert any(t["key"] == "hgb" and t["note"] for t in d["analysis"]["trends"])  # compared with seeded history
    assert d["report"]["explanation"]
    hist = c.get("/api/hemoscan/history").json()
    assert len(hist["series"]["hgb"]) >= 3
    assert "Haemoglobin" in c.get("/api/hemoscan/export.csv").text
    assert "for discussion with a healthcare professional" in c.get(f"/api/hemoscan/reports/{rid}/summary").text
    assert c.get(f"/api/hemoscan/reports/{rid}/page/0").headers["content-type"] == "image/png"
    assert c.get("/api/eligibility").json()["hemoscan"]["ok"] is False


def test_bad_values_and_units_are_rejected():
    c = client()
    rid = c.post("/api/hemoscan/reports/manual", json={"report_date": "2026-01-10"}, headers=H).json()["id"]
    d = c.get(f"/api/hemoscan/reports/{rid}").json()
    bad_unit = confirm_body(d, report_date="2026-01-10", results=[{"key": "hgb", "value": 12, "unit": "fL"}])
    assert c.post(f"/api/hemoscan/reports/{rid}/confirm", json=bad_unit, headers=H).status_code == 422
    no_unit = confirm_body(d, report_date="2026-01-10", results=[{"key": "hgb", "value": 12}])
    assert c.post(f"/api/hemoscan/reports/{rid}/confirm", json=no_unit, headers=H).status_code == 422
    silly = confirm_body(d, report_date="2026-01-10", results=[{"key": "hgb", "value": 120, "unit": "g/dL"}])
    assert c.post(f"/api/hemoscan/reports/{rid}/confirm", json=silly, headers=H).status_code == 422
    ok = confirm_body(d, report_date="2026-01-10", results=[{"key": "hgb", "value": 128, "unit": "g/L"}])
    assert c.post(f"/api/hemoscan/reports/{rid}/confirm", json=ok, headers=H).status_code == 200
    assert c.delete(f"/api/hemoscan/reports/{rid}", headers=H).status_code == 200


def test_rejects_non_pdf_and_requires_consent():
    c = client()
    r1 = c.post("/api/hemoscan/reports/upload", files={"file": ("a.pdf", b"hello", "application/pdf")},
                data={"consent": "true"}, headers=H)
    assert r1.status_code == 415
    r2 = c.post("/api/hemoscan/reports/upload", files={"file": ("a.pdf", samples.make("latest"), "application/pdf")},
                headers=H)
    assert r2.status_code == 422


def test_reports_are_private_to_their_owner():
    owner = client()
    rid = upload(owner)["id"]
    other = TestClient(app)
    other.post("/api/signup", json={"agree_privacy": True, "name": "Other Donor", "email": "other.hemoscan@example.com", "password": "Password1!",
                                    "blood_type": "A+", "city": "Kuala Lumpur"}, headers=H)
    assert other.get(f"/api/hemoscan/reports/{rid}").status_code == 404
    assert other.get(f"/api/hemoscan/reports/{rid}/file").status_code == 404
    assert other.delete(f"/api/hemoscan/reports/{rid}", headers=H).status_code == 404
    assert client("organizer@demo.com").get("/api/hemoscan/reports").status_code == 403
    assert client("admin@demo.com").get(f"/api/hemoscan/reports/{rid}").status_code == 403
    assert owner.delete(f"/api/hemoscan/reports/{rid}", headers=H).status_code == 200
    assert owner.get(f"/api/hemoscan/reports/{rid}").status_code == 404
