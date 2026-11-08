"""
HemoScan rules engine — transparent, deterministic, separate from the language model.

Order of work:
  1. Flag each value against the lab's reference interval (or a typical adult range if the report had none).
  2. Urgent values: a few thresholds where people are usually advised to contact a doctor promptly.
  3. Pattern rules: documented combinations (e.g. low Hb + low MCV). Each rule lists exactly which values
     triggered it, what it CAN be associated with (never a diagnosis), what doctors usually check next,
     and the published sources it is based on.
  4. Trends against the person's previous confirmed report.
  5. Donation note for blood donors (Hb vs a typical donation threshold, frequent-donor iron).

!! REVIEW STATUS: these rules are written from the cited public guidelines for an educational prototype.
!! They have NOT been reviewed by a clinician. Ask a doctor or haematology lecturer to review them,
!! then fill in REVIEW below. Thresholds marked "placeholder" must be checked.
"""
from __future__ import annotations

from typing import Callable

from .biomarkers import BY_KEY, default_range

RULES_VERSION = "2026.11-draft"
REVIEW = {"status": "Pending clinician review", "reviewed_by": None, "reviewed_on": None}

REFS = {
    "who_hb": "WHO (2024). Guideline on haemoglobin cutoffs to define anaemia in individuals and populations.",
    "nice_ida": "NICE Clinical Knowledge Summaries: Anaemia — iron deficiency.",
    "bsh_iron": "British Society for Haematology (2022). Guideline for the laboratory diagnosis of iron deficiency in adults (excluding pregnancy) and children.",
    "mentzer": "Mentzer WC Jr (1973). Differentiation of iron deficiency from thalassaemia trait. The Lancet.",
    "nice_b12": "NICE Clinical Knowledge Summaries: Anaemia — B12 and folate deficiency.",
    "dengue_my": "Ministry of Health Malaysia. Clinical Practice Guidelines: Management of Dengue Infection in Adults (3rd ed., 2015).",
    "fbc_general": "General FBC interpretation, e.g. Lab Tests Online (labtestsonline.org.uk): Full blood count.",
}

# placeholder thresholds — a clinician must confirm
URGENT = [
    ("hgb", "<", 7.0, "Haemoglobin is very low."),
    ("plt", "<", 50, "Platelets are very low, which can increase bleeding risk."),
    ("plt", ">", 1000, "Platelets are very high."),
    ("wbc", "<", 2.0, "White cells are very low."),
    ("wbc", ">", 30, "White cells are very high."),
    ("neut", "<", 0.5, "Neutrophils are very low, which raises infection risk."),
]
URGENT_ADVICE = ("Values like this can need prompt medical attention. Please contact your doctor or clinic today. "
                 "If you feel unwell — for example fever, bleeding, chest pain, breathlessness or fainting — seek urgent care.")
DONATION_HB_THRESHOLD = 12.5  # g/dL — PDN donor form records "≥ 12.5 g/dL" (finger-prick check on the day)


def _status(value: float, lo: float | None, hi: float | None) -> tuple[str, float]:
    if lo is not None and value < lo:
        return "low", round((lo - value) / lo * 100, 1) if lo else 0.0
    if hi is not None and value > hi:
        return "high", round((value - hi) / hi * 100, 1) if hi else 0.0
    return "normal", 0.0


def flag_results(results: list[dict], sex: str | None) -> list[dict]:
    out = []
    for r in results:
        if r.get("value") is None:
            continue
        lo, hi, src = r.get("ref_low"), r.get("ref_high"), "lab"
        if lo is None and hi is None:
            lo, hi = default_range(r["key"], sex)
            src = "typical adult range"
        elif lo is None or hi is None:  # lab printed only "< x" or "> x"
            dlo, dhi = default_range(r["key"], sex)
            lo, hi = (dlo if lo is None else lo), (dhi if hi is None else hi)
        status, dev = _status(r["value"], lo, hi)
        out.append({**r, "ref_low": lo, "ref_high": hi, "ref_source": src, "flag": status, "deviation_pct": dev,
                    "name": BY_KEY[r["key"]].name, "unit": BY_KEY[r["key"]].unit})
    return out


# ---------------------------------------------------------------- pattern rules


class Ctx:
    def __init__(self, flagged: list[dict]):
        self.r = {x["key"]: x for x in flagged}

    def has(self, *keys):
        return all(k in self.r for k in keys)

    def low(self, k):
        return k in self.r and self.r[k]["flag"] == "low"

    def high(self, k):
        return k in self.r and self.r[k]["flag"] == "high"

    def normal(self, k):
        return k in self.r and self.r[k]["flag"] == "normal"

    def v(self, k):
        return self.r[k]["value"] if k in self.r else None

    def show(self, k):
        x = self.r[k]
        return f"{BY_KEY[k].name.split(' (')[0]} {x['value']:g} {x['unit']} ({x['flag']}; range {x['ref_low']:g}–{x['ref_high']:g})"


Rule = dict


def _rules() -> list[Rule]:
    return [
        {
            "id": "pancytopenia", "severity": "see_doctor_soon",
            "title": "Low red cells, white cells and platelets together",
            "when": lambda c: c.low("hgb") and c.low("wbc") and c.low("plt"),
            "why": ["hgb", "wbc", "plt"],
            "associations": ["Severe infections", "Vitamin B12 or folate deficiency", "Some medicines",
                             "Bone marrow conditions (less common)"],
            "next": ["A doctor review soon", "Repeat FBC and blood film", "B12, folate and other tests your doctor chooses"],
            "refs": ["fbc_general"],
        },
        {
            "id": "microcytic_anaemia", "severity": "see_doctor",
            "title": "Low haemoglobin with small red cells (microcytic anaemia pattern)",
            "when": lambda c: c.low("hgb") and c.low("mcv"),
            "why": ["hgb", "mcv", "mch"],
            "associations": ["Iron deficiency (the most common cause; frequent blood donation and heavy periods are common reasons)",
                             "Thalassaemia trait (common in Malaysia)", "Anaemia of chronic inflammation"],
            "next": ["Ferritin / iron studies", "Haemoglobin analysis (e.g. Hb electrophoresis) if thalassaemia is suspected",
                     "Looking for a source of blood loss"],
            "refs": ["who_hb", "nice_ida", "bsh_iron"],
        },
        {
            "id": "rdw_supports_iron", "severity": "info",
            "title": "Mixed red cell sizes alongside small cells",
            "when": lambda c: c.low("mcv") and c.high("rdw"),
            "why": ["mcv", "rdw"],
            "associations": ["A high RDW with small cells is more typical of iron deficiency than of thalassaemia trait"],
            "next": ["Ferritin / iron studies confirm or rule out iron deficiency"],
            "refs": ["bsh_iron", "fbc_general"],
        },
        {
            "id": "mentzer", "severity": "info",
            "title": "Mentzer index (MCV ÷ RBC)",
            "when": lambda c: c.low("mcv") and c.has("rbc"),
            "why": ["mcv", "rbc"],
            "detail": lambda c: (f"MCV {c.v('mcv'):g} ÷ RBC {c.v('rbc'):g} = {c.v('mcv') / c.v('rbc'):.1f}. "
                                 + ("Above 13 tends to point towards iron deficiency." if c.v("mcv") / c.v("rbc") > 13
                                    else "Below 13 tends to point towards thalassaemia trait.")
                                 + " It is a screening hint only — it cannot confirm either."),
            "associations": ["Helps doctors decide which follow-up test to order first"],
            "next": ["Ferritin and/or haemoglobin analysis, as your doctor decides"],
            "refs": ["mentzer"],
        },
        {
            "id": "microcytosis_no_anaemia", "severity": "watch",
            "title": "Small red cells without anaemia",
            "when": lambda c: c.low("mcv") and not c.low("hgb") and c.has("hgb"),
            "why": ["mcv", "hgb"],
            "associations": ["Thalassaemia trait", "Early iron deficiency"],
            "next": ["Ferritin; haemoglobin analysis if ferritin is normal"],
            "refs": ["nice_ida", "fbc_general"],
        },
        {
            "id": "normocytic_anaemia", "severity": "see_doctor",
            "title": "Low haemoglobin with normal-sized red cells",
            "when": lambda c: c.low("hgb") and c.normal("mcv"),
            "why": ["hgb", "mcv"],
            "associations": ["Recent blood loss", "Long-term illness or inflammation", "Kidney disease",
                             "Mixed deficiencies (iron plus B12/folate)"],
            "next": ["Reticulocyte count", "Kidney function", "Iron, B12 and folate"],
            "refs": ["who_hb", "fbc_general"],
        },
        {
            "id": "macrocytic_anaemia", "severity": "see_doctor",
            "title": "Low haemoglobin with large red cells (macrocytic anaemia pattern)",
            "when": lambda c: c.low("hgb") and c.high("mcv"),
            "why": ["hgb", "mcv"],
            "associations": ["Vitamin B12 or folate deficiency", "Alcohol", "Liver disease", "Underactive thyroid",
                             "Some medicines"],
            "next": ["Vitamin B12 and folate", "Liver and thyroid tests"],
            "refs": ["nice_b12", "fbc_general"],
        },
        {
            "id": "macrocytosis_no_anaemia", "severity": "watch",
            "title": "Large red cells without anaemia",
            "when": lambda c: c.high("mcv") and not c.low("hgb") and c.has("hgb"),
            "why": ["mcv"],
            "associations": ["Alcohol", "B12/folate deficiency starting", "Liver or thyroid conditions", "Some medicines"],
            "next": ["B12, folate, liver and thyroid tests if your doctor thinks it is needed"],
            "refs": ["nice_b12"],
        },
        {
            "id": "high_hb", "severity": "watch",
            "title": "High haemoglobin / haematocrit",
            "when": lambda c: c.high("hgb") or c.high("hct"),
            "why": ["hgb", "hct"],
            "associations": ["Dehydration", "Smoking", "Lung or heart conditions", "Rarely, a bone marrow condition"],
            "next": ["Repeat test when well hydrated", "Doctor review if it stays high"],
            "refs": ["fbc_general"],
        },
        {
            "id": "low_plt_low_wbc", "severity": "see_doctor_soon",
            "title": "Low platelets with low white cells",
            "when": lambda c: c.low("plt") and c.low("wbc"),
            "why": ["plt", "wbc"],
            "associations": ["Viral infections — in Malaysia, dengue commonly causes this pattern, especially with fever",
                             "Some medicines", "Bone marrow conditions (less common)"],
            "next": ["See a doctor promptly if you have fever, rash, bleeding gums or abdominal pain",
                     "Repeat FBC; dengue tests (NS1 / antibodies) if your doctor suspects dengue"],
            "refs": ["dengue_my", "fbc_general"],
        },
        {
            "id": "low_plt", "severity": "see_doctor",
            "title": "Low platelets (thrombocytopenia)",
            "when": lambda c: c.low("plt") and not c.low("wbc"),
            "why": ["plt"],
            "associations": ["Viral infections (including dengue)", "Some medicines", "Immune causes",
                             "Clumping in the sample tube (a lab artefact)"],
            "next": ["Repeat FBC and blood film", "Doctor review, sooner if bleeding or fever"],
            "refs": ["dengue_my", "fbc_general"],
        },
        {
            "id": "high_plt", "severity": "watch",
            "title": "High platelets",
            "when": lambda c: c.high("plt"),
            "why": ["plt"],
            "associations": ["A reaction to infection, inflammation or iron deficiency (most common)",
                             "Rarely, a bone marrow condition"],
            "next": ["Repeat FBC after any infection settles", "Iron studies if iron deficiency is possible"],
            "refs": ["fbc_general", "bsh_iron"],
        },
        {
            "id": "neutrophilia", "severity": "watch",
            "title": "High white cells mainly from neutrophils",
            "when": lambda c: c.high("wbc") and c.high("neut"),
            "why": ["wbc", "neut"],
            "associations": ["Bacterial infection", "Inflammation", "Stress or recent exercise", "Steroid medicines", "Smoking"],
            "next": ["Doctor review if you have symptoms of infection", "Repeat FBC"],
            "refs": ["fbc_general"],
        },
        {
            "id": "lymphocytosis", "severity": "watch",
            "title": "High lymphocytes",
            "when": lambda c: c.high("lymph"),
            "why": ["lymph"],
            "associations": ["Viral infections (most common)", "Less commonly, conditions a doctor may check with a blood film"],
            "next": ["Repeat FBC after recovery from any infection"],
            "refs": ["fbc_general"],
        },
        {
            "id": "leukopenia", "severity": "see_doctor",
            "title": "Low white cells / neutrophils",
            "when": lambda c: (c.low("wbc") or c.low("neut")) and not c.low("plt"),
            "why": ["wbc", "neut"],
            "associations": ["Recent viral infection", "Some medicines",
                             "A harmless lower baseline in some people", "Bone marrow conditions (less common)"],
            "next": ["Repeat FBC", "Doctor review, sooner if you get a fever"],
            "refs": ["fbc_general"],
        },
        {
            "id": "eosinophilia", "severity": "watch",
            "title": "High eosinophils",
            "when": lambda c: c.high("eos"),
            "why": ["eos"],
            "associations": ["Allergies, eczema or asthma", "Parasite (worm) infections", "Some medicines"],
            "next": ["Doctor review if it persists or you have symptoms"],
            "refs": ["fbc_general"],
        },
        {
            "id": "isolated_low_hb", "severity": "see_doctor",
            "title": "Low haemoglobin",
            "when": lambda c: c.low("hgb") and not c.has("mcv"),
            "why": ["hgb"],
            "associations": ["Anaemia from many possible causes; red cell size (MCV) helps narrow them down"],
            "next": ["A full FBC including MCV", "Iron, B12 and folate as your doctor decides"],
            "refs": ["who_hb"],
        },
    ]


RULES = _rules()
SEVERITY_ORDER = {"urgent": 0, "see_doctor_soon": 1, "see_doctor": 2, "watch": 3, "info": 4}
SEVERITY_LABEL = {"urgent": "Contact a doctor promptly", "see_doctor_soon": "See a doctor soon",
                  "see_doctor": "Discuss with a doctor", "watch": "Worth watching", "info": "Extra context"}


def run_rules(flagged: list[dict]) -> list[dict]:
    c = Ctx(flagged)
    out = []
    for rule in RULES:
        try:
            hit = rule["when"](c)
        except (TypeError, ZeroDivisionError):
            hit = False
        if not hit:
            continue
        why = [c.show(k) for k in rule["why"] if k in c.r]
        detail: Callable | None = rule.get("detail")
        out.append({
            "id": rule["id"], "title": rule["title"], "severity": rule["severity"],
            "severity_label": SEVERITY_LABEL[rule["severity"]],
            "why": why, "detail": detail(c) if detail else None,
            "associations": rule["associations"], "next_steps": rule["next"],
            "references": [REFS[r] for r in rule["refs"]],
        })
    out.sort(key=lambda f: SEVERITY_ORDER[f["severity"]])
    return out


def urgent_values(flagged: list[dict]) -> list[dict]:
    by = {x["key"]: x for x in flagged}
    out = []
    for key, op, limit, msg in URGENT:
        x = by.get(key)
        if x and ((op == "<" and x["value"] < limit) or (op == ">" and x["value"] > limit)):
            out.append({"key": key, "value": x["value"], "unit": x["unit"], "message": msg,
                        "rule": f"{BY_KEY[key].name} {op} {limit:g} {x['unit']} (placeholder threshold)"})
    return out


TREND_KEYS = ["hgb", "mcv", "mch", "rdw", "wbc", "plt", "hct", "rbc"]


def trends(current: list[dict], previous: list[dict] | None, prev_date: str | None) -> list[dict]:
    if not previous:
        return []
    prev = {x["key"]: x for x in previous}
    out = []
    for x in current:
        k = x["key"]
        if k not in TREND_KEYS or k not in prev:
            continue
        before, now = prev[k]["value"], x["value"]
        change = now - before
        pct = (change / before * 100) if before else 0
        note = None
        if k == "hgb" and change <= -1.0:
            note = "Haemoglobin dropped by 1 g/dL or more since your last report."
        elif k == "plt" and pct <= -30:
            note = "Platelets fell by 30% or more since your last report."
        elif k == "mcv" and change <= -4:
            note = "Red cells are getting smaller over time, which can happen as iron stores fall."
        out.append({"key": k, "name": BY_KEY[k].name, "unit": x["unit"], "previous": before, "current": now,
                    "previous_date": prev_date, "change": round(change, 2), "change_pct": round(pct, 1),
                    "direction": "up" if change > 0 else "down" if change < 0 else "same", "note": note})
    return out


def donation_note(flagged: list[dict], donations_last_year: int, is_donor: bool) -> dict | None:
    if not is_donor:
        return None
    hb = next((x for x in flagged if x["key"] == "hgb"), None)
    if not hb:
        return None
    ok = hb["value"] >= DONATION_HB_THRESHOLD
    msg = (f"Your haemoglobin ({hb['value']:g} g/dL) is at or above {DONATION_HB_THRESHOLD:g} g/dL, a typical minimum for "
           "donating. The blood bank still tests it on the day." if ok else
           f"Your haemoglobin ({hb['value']:g} g/dL) is below {DONATION_HB_THRESHOLD:g} g/dL, a typical minimum for donating. "
           "Please don't book a donation until a doctor has reviewed this; the blood bank would likely defer you on the day.")
    iron = None
    mcv = next((x for x in flagged if x["key"] == "mcv"), None)
    if donations_last_year >= 3 and ((mcv and mcv["flag"] == "low") or hb["flag"] == "low"):
        iron = (f"You donated {donations_last_year} times in the last 12 months. Frequent donors can run low on iron, "
                "which fits this pattern — mention it to your doctor and ask about checking ferritin.")
    return {"hb": hb["value"], "threshold": DONATION_HB_THRESHOLD, "ok": ok, "message": msg, "frequent_donor_note": iron,
            "threshold_note": "Placeholder threshold — confirm with Pusat Darah Negara."}


def analyse(results: list[dict], sex: str | None, previous: list[dict] | None = None, previous_date: str | None = None,
            donations_last_year: int = 0, is_donor: bool = True) -> dict:
    flagged = flag_results(results, sex)
    core = [x for x in flagged if not BY_KEY[x["key"]].percent]
    urgent = urgent_values(core)
    findings = run_rules(core)
    if urgent:
        findings.insert(0, {
            "id": "urgent_values", "title": "Values that may need prompt attention", "severity": "urgent",
            "severity_label": SEVERITY_LABEL["urgent"], "why": [u["rule"] for u in urgent], "detail": URGENT_ADVICE,
            "associations": [u["message"] for u in urgent], "next_steps": ["Contact your doctor or clinic today"],
            "references": [REFS["fbc_general"]],
        })
    prev_flagged = flag_results(previous, sex) if previous else None
    return {
        "results": flagged,
        "counts": {s: sum(1 for x in core if x["flag"] == s) for s in ("normal", "low", "high")},
        "urgent": urgent,
        "findings": findings,
        "trends": trends(core, prev_flagged, previous_date),
        "donation": donation_note(core, donations_last_year, is_donor),
        "rules_version": RULES_VERSION,
        "review": REVIEW,
        "limitations": [
            "This is pattern matching on numbers, not a diagnosis. Only a doctor who knows your history can diagnose.",
            "A normal report does not rule out illness, and an out-of-range value is often harmless.",
            "Reference ranges differ between labs, ages, sex and pregnancy; we use your lab's range when it is on the report.",
            "Rules and placeholder thresholds have not yet been reviewed by a clinician.",
        ],
    }


def rule_catalog() -> list[dict]:
    return [{"id": r["id"], "title": r["title"], "severity": SEVERITY_LABEL[r["severity"]],
             "references": [REFS[x] for x in r["refs"]]} for r in RULES]
