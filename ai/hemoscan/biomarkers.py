"""
HemoScan biomarker catalogue: names, aliases, canonical units, unit conversion, typical adult
reference intervals and plausibility limits for a Full Blood Count (FBC / CBC).

!! The DEFAULT ranges are typical adult values used ONLY when a report has no reference interval.
!! Laboratories differ — the lab's own range always wins. Have a clinician review these values.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Biomarker:
    key: str
    name: str
    unit: str                      # canonical unit
    aliases: tuple[str, ...]
    default_male: tuple[float, float]
    default_female: tuple[float, float]
    plausible: tuple[float, float]  # outside this the value is almost certainly mis-read
    group: str
    explain: str                    # plain-language glossary text
    percent: bool = False           # differential count as %
    accepts: tuple[str, ...] = field(default_factory=tuple)  # unit families accepted


CATALOG: list[Biomarker] = [
    Biomarker("hgb", "Haemoglobin (Hb)", "g/dL",
              ("haemoglobin", "hemoglobin", "hgb", "hb"), (13.0, 17.0), (12.0, 15.5), (2, 25), "Red cells",
              "The protein in red cells that carries oxygen. Low Hb is called anaemia.", accepts=("g/dL", "g/L")),
    Biomarker("rbc", "Red blood cell count (RBC)", "x10^12/L",
              ("red blood cell count", "red blood cells", "red cell count", "rbc count", "erythrocytes", "rbc"),
              (4.5, 5.9), (4.0, 5.2), (1, 9), "Red cells",
              "How many red cells are in a litre of blood.", accepts=("x10^12/L",)),
    Biomarker("hct", "Haematocrit (HCT / PCV)", "%",
              ("haematocrit", "hematocrit", "packed cell volume", "hct", "pcv"), (40, 50), (36, 46), (10, 75), "Red cells",
              "The share of your blood volume made up of red cells.", accepts=("%", "L/L")),
    Biomarker("mcv", "Mean cell volume (MCV)", "fL",
              ("mean corpuscular volume", "mean cell volume", "mcv"), (80, 100), (80, 100), (50, 130), "Red cells",
              "The average size of your red cells. Small cells = microcytic; large = macrocytic.", accepts=("fL",)),
    Biomarker("mch", "Mean cell haemoglobin (MCH)", "pg",
              ("mean corpuscular hemoglobin", "mean corpuscular haemoglobin", "mean cell haemoglobin",
               "mean cell hemoglobin", "mch"), (27, 33), (27, 33), (15, 45), "Red cells",
              "The average amount of haemoglobin in each red cell.", accepts=("pg",)),
    Biomarker("mchc", "Mean cell Hb concentration (MCHC)", "g/dL",
              ("mean corpuscular hemoglobin concentration", "mean corpuscular haemoglobin concentration",
               "mean cell hb concentration", "mchc"), (32, 36), (32, 36), (25, 40), "Red cells",
              "How concentrated the haemoglobin is inside red cells.", accepts=("g/dL", "g/L")),
    Biomarker("rdw", "Red cell distribution width (RDW)", "%",
              ("red cell distribution width", "rdw-cv", "rdw cv", "rdw"), (11.5, 14.5), (11.5, 14.5), (8, 30), "Red cells",
              "How much your red cells vary in size. High RDW means mixed sizes.", accepts=("%",)),
    Biomarker("wbc", "White blood cell count (WBC)", "x10^9/L",
              ("total white cell count", "white blood cell count", "white blood cells", "white cell count",
               "total leucocyte count", "total leukocyte count", "leucocytes", "leukocytes", "wbc", "twc", "tlc"),
              (4.0, 11.0), (4.0, 11.0), (0.1, 200), "White cells",
              "Cells that fight infection.", accepts=("x10^9/L",)),
    Biomarker("neut", "Neutrophils (absolute)", "x10^9/L",
              ("absolute neutrophil count", "neutrophils", "neutrophil", "neut", "anc"), (2.0, 7.5), (2.0, 7.5), (0, 100),
              "White cells", "White cells that fight bacterial infection.", accepts=("x10^9/L",)),
    Biomarker("lymph", "Lymphocytes (absolute)", "x10^9/L",
              ("absolute lymphocyte count", "lymphocytes", "lymphocyte", "lymph"), (1.0, 4.0), (1.0, 4.0), (0, 100),
              "White cells", "White cells that fight viral infection and make antibodies.", accepts=("x10^9/L",)),
    Biomarker("mono", "Monocytes (absolute)", "x10^9/L",
              ("monocytes", "monocyte", "mono"), (0.2, 1.0), (0.2, 1.0), (0, 50), "White cells",
              "White cells that clean up damaged cells and germs.", accepts=("x10^9/L",)),
    Biomarker("eos", "Eosinophils (absolute)", "x10^9/L",
              ("eosinophils", "eosinophil", "eos"), (0.0, 0.5), (0.0, 0.5), (0, 50), "White cells",
              "White cells involved in allergies and parasite infections.", accepts=("x10^9/L",)),
    Biomarker("baso", "Basophils (absolute)", "x10^9/L",
              ("basophils", "basophil", "baso"), (0.0, 0.1), (0.0, 0.1), (0, 20), "White cells",
              "Rare white cells involved in allergic reactions.", accepts=("x10^9/L",)),
    Biomarker("plt", "Platelets (PLT)", "x10^9/L",
              ("platelet count", "platelets", "platelet", "plt", "thrombocytes"), (150, 400), (150, 400), (2, 2000),
              "Platelets", "Cell fragments that help blood clot.", accepts=("x10^9/L",)),
    Biomarker("mpv", "Mean platelet volume (MPV)", "fL",
              ("mean platelet volume", "mpv"), (7.5, 11.5), (7.5, 11.5), (4, 16), "Platelets",
              "The average size of your platelets.", accepts=("fL",)),
]

# differential counts reported as % (not analysed for patterns, kept for the record)
PERCENT_KEYS = {"neut": "neut_pct", "lymph": "lymph_pct", "mono": "mono_pct", "eos": "eos_pct", "baso": "baso_pct"}
for base, pkey in list(PERCENT_KEYS.items()):
    b = next(x for x in CATALOG if x.key == base)
    CATALOG.append(Biomarker(pkey, b.name.replace("(absolute)", "(%)"), "%", (), (0, 100), (0, 100), (0, 100),
                             b.group, b.explain, percent=True, accepts=("%",)))

BY_KEY = {b.key: b for b in CATALOG}
ORDER = [b.key for b in CATALOG]

# alias -> key, longest first so "mchc" wins over "mch" and "red cell distribution width" over "red cell"
ALIASES = sorted(((a, b.key) for b in CATALOG for a in b.aliases), key=lambda x: -len(x[0]))


# ---------------------------------------------------------------- units

UNIT_PATTERNS: list[tuple[str, str]] = [
    (r"x\s*10\s*(?:\^|e|\*)?\s*12\s*/\s*l", "x10^12/L"),
    (r"10\s*(?:\^|e|\*)\s*12\s*/\s*l", "x10^12/L"),
    (r"x\s*10\s*(?:\^|e|\*)?\s*6\s*/\s*(?:u|µ|μ)l", "x10^12/L"),
    (r"10\s*(?:\^|e|\*)\s*6\s*/\s*(?:u|µ|μ)l", "x10^12/L"),
    (r"(?:m|mil|million)\s*/\s*(?:u|µ|μ)l", "x10^12/L"),
    (r"x\s*10\s*(?:\^|e|\*)?\s*9\s*/\s*l", "x10^9/L"),
    (r"10\s*(?:\^|e|\*)\s*9\s*/\s*l", "x10^9/L"),
    (r"x\s*10\s*(?:\^|e|\*)?\s*3\s*/\s*(?:u|µ|μ)l", "x10^9/L"),
    (r"10\s*(?:\^|e|\*)\s*3\s*/\s*(?:u|µ|μ)l", "x10^9/L"),
    (r"(?:k|thou|thousand)\s*/\s*(?:u|µ|μ)l", "x10^9/L"),
    (r"/\s*nl\b", "x10^9/L"),
    (r"(?:cells\s*)?/\s*(?:u|µ|μ)l", "/uL"),
    (r"(?:cells\s*)?/\s*mm\s*(?:3|³)", "/uL"),
    (r"g\s*/\s*dl", "g/dL"),
    (r"g\s*/\s*l\b", "g/L"),
    (r"\bl\s*/\s*l\b", "L/L"),
    (r"\bfl\b", "fL"),
    (r"\bpg\b", "pg"),
    (r"%", "%"),
]
UNIT_RE = [(re.compile(p, re.I), u) for p, u in UNIT_PATTERNS]
UNIT_CHOICES = sorted({u for _, u in UNIT_PATTERNS})


def find_unit(text: str) -> tuple[str | None, str]:
    """Return (unit family, text with the unit removed)."""
    for rx, unit in UNIT_RE:
        m = rx.search(text)
        if m:
            return unit, text[: m.start()] + " " + text[m.end():]
    return None, text


def to_canonical(key: str, value: float, unit: str | None) -> tuple[float, str | None]:
    """Convert a value to the biomarker's canonical unit. Returns (value, problem or None)."""
    b = BY_KEY[key]
    if unit is None:
        return value, "missing unit"
    if unit == b.unit:
        return value, None
    if unit == "g/L" and b.unit == "g/dL":
        return value / 10, None
    if unit == "L/L" and b.unit == "%":
        return value * 100, None
    if unit == "/uL" and b.unit == "x10^9/L":
        return value / 1000, None
    if unit == "/uL" and b.unit == "x10^12/L":
        return value / 1_000_000, None
    return value, f"unexpected unit {unit} for {b.name}"


def default_range(key: str, sex: str | None) -> tuple[float, float]:
    b = BY_KEY[key]
    return b.default_female if (sex or "").lower().startswith("f") else b.default_male if (sex or "").lower().startswith("m") \
        else (min(b.default_female[0], b.default_male[0]), max(b.default_female[1], b.default_male[1]))
