"""
Photo / scanned-report reading (OCR) for HemoScan.

Engines, tried in order:
  1. RapidOCR (pip install rapidocr_onnxruntime) — works on Windows/macOS/Linux with no extra software.
  2. Tesseract through PyMuPDF — only if Tesseract is installed on the computer.
If neither is available the report falls back to manual entry beside the photo.

OCR is never trusted blindly: every value read this way is marked at most "Check" (medium confidence),
unreadable units are flagged, and the user must confirm every value before analysis.
"""
from __future__ import annotations

import math
import os
import re
from functools import lru_cache

import pymupdf

from difflib import SequenceMatcher

from .biomarkers import ALIASES, BY_KEY
from .extract import parse_line, score

MAX_SIDE = 2200  # px; larger photos are scaled down before OCR

UNIT_FIXES = [  # common OCR misreads of units
    (re.compile(r"x\s*1\s*0\s*[\^4*/]?\s*(12|9|3|6)\s*/\s*([lμu]l?)", re.I), r"x10^\1/\2"),
    (re.compile(r"g\s*/\s*d\s*[l1i|]\b", re.I), "g/dL"),
    (re.compile(r"\bf\s*[l1i|]\b", re.I), "fL"),
    (re.compile(r"\bp\s*g\b", re.I), "pg"),
]
UNIT_TOKEN = re.compile(r"^(x10\^\d+/[lμu]l?|g/dl|g/l|l/l|fl|pg|%|/ul|/μl|10\^\d+/[lμu]l?)$", re.I)
GARBAGE = re.compile(r"^(?=\S*[a-z])(?=\S*\d)\S+$", re.I)  # tokens mixing letters and digits, e.g. "7P/6"


@lru_cache(maxsize=1)
def _rapid():
    try:
        from rapidocr_onnxruntime import RapidOCR  # type: ignore
    except Exception:  # not installed or failed to load
        return None
    try:
        return RapidOCR()
    except Exception:
        return None


def _tesseract_ok() -> bool:
    try:
        return bool(pymupdf.get_tessdata())
    except Exception:
        return False


def available() -> str | None:
    if os.getenv("HEMOLINK_OCR", "on").lower() in ("off", "0", "false", "no"):
        return None  # switched off (e.g. small free hosting plans) → photos fall back to manual entry
    if _rapid() is not None:
        return "RapidOCR"
    if _tesseract_ok():
        return "Tesseract"
    return None


def _boxes_rapid(png: bytes) -> list[dict]:
    res, _ = _rapid()(png)
    out = []
    for pts, text, conf in res or []:
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        out.append({"text": text, "conf": float(conf), "x0": min(xs), "y0": min(ys), "x1": max(xs), "y1": max(ys),
                    "angle": math.atan2(pts[1][1] - pts[0][1], pts[1][0] - pts[0][0]) if len(pts) > 1 else 0.0})
    return out


def _boxes_tesseract(page: pymupdf.Page) -> list[dict]:
    tp = page.get_textpage_ocr(dpi=200, full=True)
    words = page.get_text("words", textpage=tp)
    return [{"text": w[4], "conf": 0.8, "x0": w[0], "y0": w[1], "x1": w[2], "y1": w[3], "angle": 0.0} for w in words]


def _lines(boxes: list[dict]) -> list[dict]:
    """Group OCR boxes into text rows, correcting for a slightly tilted photo."""
    if not boxes:
        return []
    wide = sorted((b for b in boxes if b["x1"] - b["x0"] > 60), key=lambda b: b["angle"])
    angle = wide[len(wide) // 2]["angle"] if wide else 0.0
    ca, sa = math.cos(-angle), math.sin(-angle)
    for b in boxes:
        cx, cy = (b["x0"] + b["x1"]) / 2, (b["y0"] + b["y1"]) / 2
        b["ry"] = cx * sa + cy * ca  # y after undoing the tilt
        b["rx"] = cx * ca - cy * sa
    heights = sorted(b["y1"] - b["y0"] for b in boxes)
    tol = max(6.0, heights[len(heights) // 2] * 0.55)
    rows: list[list[dict]] = []
    for b in sorted(boxes, key=lambda b: b["ry"]):
        if rows and abs(rows[-1][-1]["ry"] - b["ry"]) <= tol:
            rows[-1].append(b)
        else:
            rows.append([b])
    out = []
    for r in rows:
        r.sort(key=lambda b: b["rx"])
        out.append({"text": " ".join(b["text"] for b in r), "boxes": r,
                    "conf": min(b["conf"] for b in r)})
    return out


SQUASHED = sorted({(a.replace(" ", ""), a) for a, _ in ALIASES if len(a) >= 3}, key=lambda x: -len(x[0]))


def fix_label(text: str) -> str:
    """OCR often drops spaces ("RedBloodCellCount") or a letter ("Eosinophis"): map the label back to a known name."""
    m = re.match(r"^([A-Za-z][A-Za-z ()/%.-]*?)(?=\s*[\d<>]|$)", text)
    if not m:
        return text
    label, rest = m.group(1), text[m.end():]
    squashed = re.sub(r"[^a-z%]", "", label.lower())
    for sq, alias in SQUASHED:
        if squashed == sq or (squashed.startswith(sq) and len(sq) >= 6):
            return alias + " " + rest
    best = max(SQUASHED, key=lambda x: SequenceMatcher(None, squashed, x[0]).ratio())
    if len(squashed) >= 5 and SequenceMatcher(None, squashed, best[0]).ratio() >= 0.86:
        return best[1] + " " + rest
    return text


def clean(text: str) -> str:
    text = fix_label(text)
    for rx, rep in UNIT_FIXES:
        text = rx.sub(rep, text)
    toks = []
    for t in text.split():
        if GARBAGE.match(t) and not UNIT_TOKEN.match(t) and not re.match(r"^[\d.]+-[\d.]+$", t):
            continue  # drop unreadable fragments instead of mistaking them for numbers
        toks.append(t)
    return " ".join(toks)


def read_page(page: pymupdf.Page) -> tuple[list[dict], list[str], str | None]:
    """OCR one PDF page. Returns (scored items with bboxes in page points, all text rows, engine)."""
    engine = available()
    if engine is None:
        return [], [], None
    if engine == "RapidOCR":
        zoom = min(200 / 72, MAX_SIDE / max(page.rect.width, page.rect.height))
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
        boxes = _boxes_rapid(pix.tobytes("png"))
        scale = 1 / zoom
    else:
        boxes = _boxes_tesseract(page)
        scale = 1.0
    found: dict[str, dict] = {}
    texts = []
    for line in _lines(boxes):
        texts.append(line["text"])
        item = parse_line(clean(line["text"]))
        if not item:
            continue
        guessed_unit = False
        if item["unit"] is None:  # unit unreadable: propose the standard unit, but flag it
            item["unit"] = BY_KEY[item["key"]].unit
            guessed_unit = True
        s = score(item)
        bs = line["boxes"]
        s["bbox"] = [round(v * scale, 1) for v in (min(b["x0"] for b in bs), min(b["y0"] for b in bs),
                                                   max(b["x1"] for b in bs), max(b["y1"] for b in bs))]
        vb = next((b for b in bs if b["text"].strip("*:;,()HL ") == item["raw_value"]), None)
        s["value_bbox"] = [round(v * scale, 1) for v in (vb["x0"], vb["y0"], vb["x1"], vb["y1"])] if vb else None
        s["page"] = page.number
        conf = min(s["confidence"], 0.75, line["conf"])
        problems = list(s["problems"])  # the page banner already says every OCR value must be checked
        if guessed_unit:
            conf = min(conf, 0.5)
            problems.insert(0, f"Unit couldn't be read — we assumed {BY_KEY[item['key']].unit}. Please check.")
        s.update(confidence=round(conf, 2), confidence_level="medium" if conf >= 0.55 else "low",
                 problems=problems, ocr=True)
        if s["key"] not in found or s["confidence"] > found[s["key"]]["confidence"]:
            found[s["key"]] = s
    return list(found.values()), texts, engine
