"""
PDF extraction for FBC/CBC reports (text-based PDFs only).

1. PyMuPDF reads every word with its position; words on the same baseline are joined into rows,
   so table layouts and "label: value unit (range)" layouts both become one line per test.
2. Each row is matched against the biomarker aliases, then the unit, the reference interval,
   any H/L flag and the value are pulled out.
3. Values and ranges are converted to canonical units (e.g. g/L -> g/dL) and scored for confidence.
Scanned (image-only) reports have no text layer: we return scanned=True and the user types the
values in. We never guess numbers from images.
"""
from __future__ import annotations

import re
from datetime import date

import pymupdf

from .biomarkers import ALIASES, BY_KEY, ORDER, PERCENT_KEYS, find_unit, to_canonical

MAX_PAGES = 10
OCR_PAGES = 3  # OCR is slower; read at most the first 3 pages of a scanned report
CORE = ["hgb", "rbc", "hct", "mcv", "mch", "mchc", "rdw", "wbc", "plt"]

RANGE_RE = re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*(\d+(?:\.\d+)?)(?![\d.])")
UPPER_RE = re.compile(r"<\s*=?\s*(\d+(?:\.\d+)?)")
LOWER_RE = re.compile(r">\s*=?\s*(\d+(?:\.\d+)?)")
FLAG_RE = re.compile(r"(?<![a-z])(hh|ll|high|low|h|l|critical)(?![a-z])|\*")
NUM_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?![\w.])")
DATE_RE = re.compile(
    r"(?:collected|collection|sample|specimen|reported|report|date)[^\n\d]{0,25}"
    r"(\d{4}-\d{2}-\d{2}|\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})", re.I)
SEX_RE = re.compile(r"\b(?:sex|gender)\s*[:\-]?\s*(male|female|m|f)\b", re.I)
MONTHS = {m: i + 1 for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}


class ExtractionError(ValueError):
    pass


def _parse_date(s: str) -> str | None:
    s = s.strip()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
            return date.fromisoformat(s).isoformat()
        m = re.fullmatch(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})", s)
        if m:  # Malaysian reports use day/month/year
            d, mo, y = int(m[1]), int(m[2]), int(m[3])
            return date(y + 2000 if y < 100 else y, mo, d).isoformat()
        m = re.fullmatch(r"(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})", s)
        if m and m[2][:3].lower() in MONTHS:
            return date(int(m[3]), MONTHS[m[2][:3].lower()], int(m[1])).isoformat()
    except ValueError:
        return None
    return None


def _rows(page) -> list[tuple[str, list]]:
    """Join words that sit on the same baseline into one text row (keeps word boxes)."""
    words = sorted(page.get_text("words"), key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    rows: list[dict] = []
    for w in words:
        yc = (w[1] + w[3]) / 2
        if rows and abs(rows[-1]["y"] - yc) <= 3:
            rows[-1]["words"].append(w)
        else:
            rows.append({"y": yc, "words": [w]})
    out = []
    for r in rows:
        ws = sorted(r["words"], key=lambda w: w[0])
        out.append((" ".join(w[4] for w in ws), ws))
    return out


def parse_line(text: str) -> dict | None:
    low = text.lower().strip()
    key = None
    for alias, k in ALIASES:
        m = re.match(r"^[\W_]*" + re.escape(alias) + r"(?![a-z])", low)
        if m:
            key, rest = k, low[m.end():]
            break
    if key is None:
        return None
    unit, rest = find_unit(rest)
    ref_low = ref_high = None
    m = RANGE_RE.search(rest)
    if m:
        ref_low, ref_high = float(m[1]), float(m[2])
        rest = rest[: m.start()] + " " + rest[m.end():]
    else:
        m = UPPER_RE.search(rest)
        if m:
            ref_low, ref_high = 0.0, float(m[1])
            rest = rest[: m.start()] + " " + rest[m.end():]
        else:
            m = LOWER_RE.search(rest)
            if m:
                ref_low = float(m[1])
                rest = rest[: m.start()] + " " + rest[m.end():]
    flag = None
    fm = FLAG_RE.search(rest)
    if fm:
        token = (fm.group(1) or "*").lower()
        flag = "high" if token in ("h", "hh", "high") else "low" if token in ("l", "ll", "low") else "abnormal"
        rest = rest[: fm.start()] + " " + rest[fm.end():]
    nums = NUM_RE.findall(rest)
    if not nums:
        return None
    if key in PERCENT_KEYS and unit == "%":
        key = PERCENT_KEYS[key]
    return {"key": key, "raw_value": nums[0], "value": float(nums[0]), "unit": unit, "ref_low": ref_low,
            "ref_high": ref_high, "lab_flag": flag, "ambiguous": len(nums) > 1, "raw_text": text.strip()}


def score(item: dict) -> dict:
    """Convert to canonical units and score how much we trust the reading."""
    key = item["key"]
    b = BY_KEY[key]
    problems: list[str] = []
    conf = 1.0
    value, problem = to_canonical(key, item["value"], item["unit"])
    lo = hi = None
    if item["ref_low"] is not None:
        lo, _ = to_canonical(key, item["ref_low"], item["unit"])
    if item["ref_high"] is not None:
        hi, _ = to_canonical(key, item["ref_high"], item["unit"])
    if problem == "missing unit":
        conf -= 0.35
        problems.append(f"Unit missing — the expected unit is {b.unit}. Please confirm.")
    elif problem:
        conf -= 0.3
        problems.append(problem.capitalize() + ". Please check.")
    if lo is None and hi is None:
        conf -= 0.15
        problems.append("No reference range found — a typical adult range will be used.")
    if item.get("ambiguous"):
        conf -= 0.1
        problems.append("More than one number on this line.")
    pl, ph = b.plausible
    if not (pl <= value <= ph):
        conf = min(conf, 0.3)
        problems.append(f"{value:g} {b.unit} is outside what is physically plausible — likely a reading error.")
    level = "high" if conf >= 0.8 else "medium" if conf >= 0.55 else "low"
    return {**item, "value": round(value, 3), "unit": b.unit if problem in (None,) else item["unit"],
            "canonical_unit": b.unit, "ref_low": None if lo is None else round(lo, 3),
            "ref_high": None if hi is None else round(hi, 3), "confidence": round(max(conf, 0), 2),
            "confidence_level": level, "problems": problems, "name": b.name}


def extract(pdf_bytes: bytes, photo: bool = False) -> dict:
    try:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:  # corrupt or not a PDF
        raise ExtractionError("This file could not be opened as a PDF.") from exc
    if doc.needs_pass:
        raise ExtractionError("This PDF is password-protected. Please upload an unlocked copy.")
    if doc.page_count > MAX_PAGES:
        raise ExtractionError(f"Reports longer than {MAX_PAGES} pages are not supported.")

    pages, found, all_text, chars = [], {}, [], 0
    for pno, page in enumerate(doc):
        pages.append({"width": page.rect.width, "height": page.rect.height})
        for text, words in _rows(page):
            chars += len(text)
            all_text.append(text)
            item = parse_line(text)
            if not item:
                continue
            x0 = min(w[0] for w in words)
            y0 = min(w[1] for w in words)
            x1 = max(w[2] for w in words)
            y1 = max(w[3] for w in words)
            vb = next((w[:4] for w in words if w[4].strip("*:;,()") == item["raw_value"]), None)
            item.update(page=pno, bbox=[round(v, 1) for v in (x0, y0, x1, y1)],
                        value_bbox=[round(v, 1) for v in vb] if vb else None)
            scored = score(item)
            if scored["key"] not in found or scored["confidence"] > found[scored["key"]]["confidence"]:
                found[scored["key"]] = scored

    scanned = chars < 40
    engine = None
    if scanned:  # no text layer: try OCR (photo or scanned PDF); never trusted without the user's check
        from .ocr import read_page
        for page in list(doc)[:OCR_PAGES]:
            items, texts, engine = read_page(page)
            all_text.extend(texts)
            for it in items:
                if it["key"] not in found or it["confidence"] > found[it["key"]]["confidence"]:
                    found[it["key"]] = it
            if engine is None:
                break
    doc.close()

    text = "\n".join(all_text)
    d = DATE_RE.search(text)
    s = SEX_RE.search(text)
    lab = "" if scanned else next((t for t in all_text[:3] if 4 < len(t) < 80 and not any(ch.isdigit() for ch in t)), "")
    items = [found[k] for k in ORDER if k in found]
    warnings = []
    what = "photo" if photo else "scanned image"
    if scanned and items:
        warnings.append(f"Read from a {what} with OCR ({engine}). Every value is marked “Check” — compare each one "
                        "with your report before confirming.")
    elif scanned and engine:
        warnings.append(f"We couldn't read any blood count values from this {what}. Please type them in — the image "
                        "is shown beside the form.")
    elif scanned:
        warnings.append(f"This is a {what} and no OCR reader is installed, so HemoScan won't guess the numbers. "
                        "Please type the values in — the image is shown beside the form. "
                        "(Install rapidocr_onnxruntime to read photos automatically.)")
    elif not items:
        warnings.append("No full blood count tests were recognised in this PDF. Please enter the values manually.")
    missing = [k for k in CORE if k not in found]
    return {
        "scanned": scanned,
        "photo": photo,
        "ocr": engine if scanned and items else None,
        "needs_manual": not items,
        "pages": pages,
        "items": items,
        "missing": missing,
        "meta": {"report_date": _parse_date(d[1]) if d else None,
                 "sex": ("female" if s[1].lower().startswith("f") else "male") if s else None,
                 "lab_name": lab.title() if lab.isupper() else lab},
        "warnings": warnings,
    }


IMAGE_TYPES = {"image/jpeg": "jpeg", "image/jpg": "jpeg", "image/png": "png", "image/webp": "webp"}


def extract_image(img: bytes, content_type: str) -> tuple[bytes, dict]:
    """A photo of a report: store it as a one-page PDF (so the viewer and highlights work), then OCR it."""
    kind = IMAGE_TYPES.get((content_type or "").lower())
    if not kind:
        raise ExtractionError("Please use a JPG, PNG or WebP photo.")
    try:
        src = pymupdf.open(stream=img, filetype=kind)
        pdf = src.convert_to_pdf()
        src.close()
    except Exception as exc:
        raise ExtractionError("This photo could not be opened.") from exc
    return pdf, extract(pdf, photo=True)
