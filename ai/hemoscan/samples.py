"""
Fictional sample FBC reports (PDF) for demos and tests, generated with PyMuPDF.

  * latest   — table layout, iron-deficiency-like pattern (low Hb, low MCV, high RDW)
  * dengue   — different layout, SI units in g/L and x10^3/uL (tests unit conversion), low platelets + low WBC
  * scanned  — image-only PDF (no text layer) → the app must ask for manual entry
  * history1 / history2 — earlier reports for the demo donor's trend chart
All names and values are invented. Dates are relative to today so the demo always lines up.
"""
from __future__ import annotations

from datetime import date, timedelta

import pymupdf

LAB = "KLANG VALLEY DEMO LABORATORY (FICTIONAL)"

# (label, value, flag, unit, range)
HISTORY1 = [("Haemoglobin", "13.4", "", "g/dL", "12.0 - 15.5"), ("Red Blood Cell Count", "4.62", "", "x10^12/L", "4.0 - 5.2"),
            ("Haematocrit", "40.1", "", "%", "36 - 46"), ("MCV", "88.0", "", "fL", "80 - 100"), ("MCH", "29.5", "", "pg", "27 - 33"),
            ("MCHC", "33.5", "", "g/dL", "32 - 36"), ("RDW", "12.8", "", "%", "11.5 - 14.5"),
            ("White Blood Cell Count", "6.2", "", "x10^9/L", "4.0 - 11.0"), ("Neutrophils", "3.4", "", "x10^9/L", "2.0 - 7.5"),
            ("Lymphocytes", "2.1", "", "x10^9/L", "1.0 - 4.0"), ("Monocytes", "0.5", "", "x10^9/L", "0.2 - 1.0"),
            ("Eosinophils", "0.15", "", "x10^9/L", "0.0 - 0.5"), ("Basophils", "0.03", "", "x10^9/L", "0.0 - 0.1"),
            ("Platelet Count", "265", "", "x10^9/L", "150 - 400")]
HISTORY2 = [("Haemoglobin", "12.3", "", "g/dL", "12.0 - 15.5"), ("Red Blood Cell Count", "4.50", "", "x10^12/L", "4.0 - 5.2"),
            ("Haematocrit", "37.5", "", "%", "36 - 46"), ("MCV", "82.0", "", "fL", "80 - 100"), ("MCH", "27.4", "", "pg", "27 - 33"),
            ("MCHC", "32.8", "", "g/dL", "32 - 36"), ("RDW", "14.2", "", "%", "11.5 - 14.5"),
            ("White Blood Cell Count", "5.8", "", "x10^9/L", "4.0 - 11.0"), ("Neutrophils", "3.1", "", "x10^9/L", "2.0 - 7.5"),
            ("Lymphocytes", "2.0", "", "x10^9/L", "1.0 - 4.0"), ("Monocytes", "0.45", "", "x10^9/L", "0.2 - 1.0"),
            ("Eosinophils", "0.2", "", "x10^9/L", "0.0 - 0.5"), ("Basophils", "0.03", "", "x10^9/L", "0.0 - 0.1"),
            ("Platelet Count", "290", "", "x10^9/L", "150 - 400")]
LATEST = [("Haemoglobin", "11.2", "L", "g/dL", "12.0 - 15.5"), ("Red Blood Cell Count", "4.52", "", "x10^12/L", "4.0 - 5.2"),
          ("Haematocrit", "34.6", "L", "%", "36 - 46"), ("MCV", "76.0", "L", "fL", "80 - 100"), ("MCH", "24.8", "L", "pg", "27 - 33"),
          ("MCHC", "31.2", "L", "g/dL", "32 - 36"), ("RDW", "16.1", "H", "%", "11.5 - 14.5"),
          ("White Blood Cell Count", "6.4", "", "x10^9/L", "4.0 - 11.0"), ("Neutrophils", "3.9", "", "x10^9/L", "2.0 - 7.5"),
          ("Lymphocytes", "1.8", "", "x10^9/L", "1.0 - 4.0"), ("Monocytes", "0.5", "", "x10^9/L", "0.2 - 1.0"),
          ("Eosinophils", "0.18", "", "x10^9/L", "0.0 - 0.5"), ("Basophils", "0.02", "", "x10^9/L", "0.0 - 0.1"),
          ("Platelet Count", "412", "H", "x10^9/L", "150 - 400"), ("MPV", "9.8", "", "fL", "7.5 - 11.5")]
DENGUE = [("Hemoglobin", "138", "g/L", "120-155"), ("Hematocrit", "0.44", "L/L", "0.36-0.46"), ("RBC", "4.80", "x10^12/L", "4.0-5.2"),
          ("MCV", "90", "fL", "80-100"), ("MCH", "29.0", "pg", "27-33"), ("MCHC", "325", "g/L", "320-360"),
          ("WBC", "2.6", "x10^3/uL", "4.0-11.0"), ("Neutrophils %", "48", "%", "40-75"), ("Lymphocytes %", "41", "%", "20-45"),
          ("Platelets", "58", "x10^3/uL", "150-400")]


def _dmy(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def _table_pdf(rows, collected: date, title: str = "FULL BLOOD COUNT (FBC)") -> pymupdf.Document:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    y = 60
    page.insert_text((50, y), LAB, fontsize=13, fontname="hebo")
    page.insert_text((50, y + 16), "Hematology Department  |  This is a sample document for software testing only", fontsize=8)
    y += 44
    for label, val in [("Patient", "Amira Hassan (DEMO)"), ("Sex", "Female"), ("Age", "25 Y"),
                       ("Collected", _dmy(collected)), ("Reported", _dmy(collected + timedelta(days=1)))]:
        page.insert_text((50, y), f"{label}:", fontsize=9, fontname="hebo")
        page.insert_text((120, y), val, fontsize=9)
        y += 14
    y += 12
    page.insert_text((50, y), title, fontsize=11, fontname="hebo")
    y += 22
    cols = [50, 250, 315, 350, 450]
    for x, h in zip(cols, ["Test", "Result", "Flag", "Units", "Reference Range"]):
        page.insert_text((x, y), h, fontsize=9, fontname="hebo")
    page.draw_line((50, y + 5), (545, y + 5), color=(0.6, 0.6, 0.6), width=0.6)
    y += 20
    for label, value, flag, unit, rng in rows:
        for x, txt, bold in zip(cols, [label, value, flag, unit, rng], [False, True, True, False, False]):
            if txt:
                page.insert_text((x, y), txt, fontsize=9, fontname="hebo" if bold else "helv")
        y += 17
    page.insert_text((50, y + 20), "Results should be interpreted together with clinical findings. -- END OF REPORT --", fontsize=8)
    return doc


def _inline_pdf(rows, collected: date) -> pymupdf.Document:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 60), "SUNRISE CLINIC LAB SERVICES (FICTIONAL)", fontsize=13, fontname="hebo")
    page.insert_text((50, 84), f"Name: Amira Hassan (DEMO)    Gender: F    Date Collected: {collected.isoformat()}", fontsize=9)
    page.insert_text((50, 110), "Complete Blood Count", fontsize=11, fontname="hebo")
    y = 136
    for label, value, unit, rng in rows:
        page.insert_text((50, y), f"{label}", fontsize=10)
        page.insert_text((220, y), f"{value} {unit}", fontsize=10, fontname="hebo")
        page.insert_text((360, y), f"Ref: {rng}", fontsize=10)
        y += 20
    return doc


def make(name: str, today: date | None = None) -> bytes:
    today = today or date.today()
    if name == "latest":
        doc = _table_pdf(LATEST, today - timedelta(days=3))
    elif name == "history1":
        doc = _table_pdf(HISTORY1, today - timedelta(days=400))
    elif name == "history2":
        doc = _table_pdf(HISTORY2, today - timedelta(days=120))
    elif name == "dengue":
        doc = _inline_pdf(DENGUE, today - timedelta(days=1))
    elif name == "photo":  # a slightly tilted phone photo of the paper report (JPEG)
        src = _table_pdf(LATEST, today - timedelta(days=3))
        pix = src[0].get_pixmap(matrix=pymupdf.Matrix(150 / 72, 150 / 72).prerotate(1.5))
        data = pix.tobytes("jpg", jpg_quality=82)
        src.close()
        return data
    elif name == "scanned":
        src = _table_pdf(LATEST, today - timedelta(days=3))
        pix = src[0].get_pixmap(dpi=110)
        doc = pymupdf.open()
        page = doc.new_page(width=595, height=842)
        page.insert_image(page.rect, stream=pix.tobytes("png"))
    else:
        raise KeyError(name)
    data = doc.tobytes()
    doc.close()
    return data


SAMPLES = {  # name: (title, subtitle, how to use it)
    "latest": ("Latest FBC", "Table layout · PDF", "pdf"),
    "dengue": ("SI-unit FBC", "g/L and x10³/µL · PDF", "pdf"),
    "scanned": ("Scanned report", "Image-only PDF · OCR", "pdf"),
    "photo": ("Phone photo", "Paper report · JPG", "photo"),
}
