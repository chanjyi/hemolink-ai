"""
HemoCare Medication History — the donor's own medicine list, checked against donation waiting periods.

The waiting periods below are EXAMPLES taken from published US blood-service lists (see drugs.com reference in
knowledge.py). Antibiotics use Pusat Darah Negara's 2-week rule (checked Nov 2026). The other drugs are not listed
publicly by PDN, so treat them as examples — screening staff decide.
"""
from __future__ import annotations

import re
from datetime import date, timedelta

PLACEHOLDER = "Example waiting periods from other blood services — confirm with Pusat Darah Negara."

# key: (label, keywords, kind, days_after_last_dose, note)
#   kind "wait"  → no donation while taking it and for `days` after the last dose
#   kind "tell"  → usually fine for whole blood, but tell the screening staff
#   kind "ok"    → usually no effect on donating
CATEGORIES: dict[str, tuple[str, list[str], str, int | None, str]] = {
    "antibiotic": ("Antibiotics", ["amoxicillin", "augmentin", "cloxacillin", "cephalexin", "cefuroxime", "azithromycin",
                                  "clarithromycin", "erythromycin", "doxycycline", "ciprofloxacin", "levofloxacin",
                                  "metronidazole", "bactrim", "co-trimoxazole", "penicillin", "antibiotic"],
                   "wait", 14, "PDN: wait 2 weeks after the last dose, and be fully well."),
    "isotretinoin": ("Isotretinoin (acne)", ["isotretinoin", "accutane", "roaccutane", "acnotin", "absorica"],
                     "wait", 30, "Could harm an unborn baby if a pregnant patient received the blood."),
    "finasteride": ("Finasteride (hair loss / prostate)", ["finasteride", "propecia", "proscar"],
                    "wait", 30, "Could harm an unborn baby if a pregnant patient received the blood."),
    "dutasteride": ("Dutasteride (prostate)", ["dutasteride", "avodart", "jalyn"],
                    "wait", 183, "Stays in the body for months."),
    "acitretin": ("Acitretin (psoriasis)", ["acitretin", "soriatane", "neotigason"],
                  "wait", 1095, "Stays in the body for years."),
    "anticoagulant_short": ("Blood thinner (rivaroxaban, apixaban, dabigatran, enoxaparin)",
                            ["rivaroxaban", "xarelto", "apixaban", "eliquis", "dabigatran", "pradaxa", "edoxaban",
                             "enoxaparin", "clexane", "lovenox"],
                            "wait", 2, "Affects clotting."),
    "anticoagulant_long": ("Blood thinner (warfarin, heparin)", ["warfarin", "coumadin", "heparin", "fondaparinux"],
                           "wait", 7, "Affects clotting."),
    "antiplatelet": ("Antiplatelet (clopidogrel, ticagrelor, prasugrel)",
                     ["clopidogrel", "plavix", "ticagrelor", "brilinta", "prasugrel", "effient", "ticlopidine"],
                     "tell", None, "Often fine for whole blood, but not for platelet donation — tell the staff."),
    "aspirin": ("Aspirin", ["aspirin", "cardiprin", "aspilets"],
                "tell", None, "Fine for whole blood in most services; matters for platelet donation."),
    "thalidomide": ("Thalidomide / lenalidomide", ["thalidomide", "lenalidomide", "revlimid"],
                    "wait", 30, "Could harm an unborn baby."),
    "mycophenolate": ("Mycophenolate", ["mycophenolate", "cellcept", "myfortic"],
                      "wait", 42, "Could harm an unborn baby."),
    "hbig": ("Hepatitis B immune globulin", ["hepatitis b immune globulin", "hbig"],
             "wait", 365, "Given after possible hepatitis B exposure."),
    "bp": ("Blood pressure medicine", ["amlodipine", "perindopril", "lisinopril", "losartan", "valsartan", "telmisartan",
                                       "nifedipine", "bisoprolol", "atenolol", "metoprolol", "hydrochlorothiazide",
                                       "indapamide"],
           "tell", None, "Usually accepted if your blood pressure is controlled — staff check it on the day."),
    "iron": ("Iron supplement", ["iron", "ferrous", "ferric", "iberet", "obimin", "sangobion", "maltofer"],
             "ok", None, "Doesn't stop you donating. Mention it if you're taking it for low haemoglobin."),
    "vitamin": ("Vitamins / folic acid", ["vitamin", "folic", "folate", "b12", "multivitamin", "calcium", "zinc"],
                "ok", None, "Usually no effect on donating."),
    "contraceptive": ("Contraceptive pill", ["contraceptive", "yasmin", "diane", "microgynon", "marvelon"],
                      "ok", None, "Usually no effect on donating."),
    "paracetamol": ("Paracetamol", ["paracetamol", "panadol", "acetaminophen"], "ok", None,
                    "Usually no effect on donating (but you must be well on the day)."),
    "other": ("Other / not listed", [], "tell", None, "Not in HemoCare's list — tell the screening staff."),
}

CATEGORY_CHOICES = [{"key": k, "label": v[0]} for k, v in CATEGORIES.items()]


def detect(name: str) -> str:
    n = name.lower()
    best, best_len = "other", 0
    for key, (_, words, *_r) in CATEGORIES.items():
        for w in words:
            if len(w) > best_len and re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", n):
                best, best_len = key, len(w)
    return best


def status(med: dict, today: date | None = None) -> dict:
    """What a medicine means for donating today."""
    today = today or date.today()
    key = med.get("category") if med.get("category") in CATEGORIES else detect(med["name"])
    label, _w, kind, days, note = CATEGORIES[key]
    end = date.fromisoformat(med["end_date"]) if med.get("end_date") else None
    ongoing = end is None or end >= today
    out = {"category": key, "category_label": label, "kind": kind, "note": note, "ongoing": ongoing,
           "until": None, "state": "ok"}
    if kind == "wait":
        until = (end + timedelta(days=days)) if end else None
        out["until"] = until.isoformat() if until else None
        if end is None:
            out.update(state="hold", message=f"Not while taking it, and for {_days(days)} after the last dose.")
        elif until > today:
            out.update(state="hold", message=f"Wait until {until.isoformat()} ({_days(days)} after the last dose).")
        else:
            out.update(state="ok", message=f"Waiting period ended on {until.isoformat()}.")
    elif kind == "tell":
        out.update(state="tell", message=note if ongoing else "Stopped — mention it if it was recent.")
    else:
        out.update(message=note)
    return out


def _days(n: int) -> str:
    if n >= 365 and n % 365 == 0:
        return f"{n // 365} year{'s' if n >= 730 else ''}"
    if n >= 28 and n % 30 in (0, 3) and n < 365:
        m = round(n / 30.4)
        return f"{m} month{'s' if m > 1 else ''}"
    if n % 7 == 0 and n >= 14:
        return f"{n // 7} weeks"
    return f"{n} day{'s' if n > 1 else ''}"


def hold(meds: list[dict], today: date | None = None) -> dict | None:
    """The medicine waiting period that applies now, if any (used by eligibility and donor matching)."""
    holds = [(m, status(m, today)) for m in meds]
    holds = [(m, s) for m, s in holds if s["state"] == "hold"]
    if not holds:
        return None
    ongoing = [m["name"] for m, s in holds if s["ongoing"] and s["until"] is None]
    until = max((s["until"] for _, s in holds if s["until"]), default=None)
    names = ", ".join(sorted({m["name"] for m, _ in holds}))
    reason = (f"You're taking {', '.join(ongoing)}, which needs a waiting period after the last dose."
              if ongoing else f"{names} needs a waiting period after the last dose (until {until}).")
    return {"ongoing": bool(ongoing), "until": until, "reason": reason + " (HemoCare · placeholder rule)",
            "medicines": sorted({m["name"] for m, _ in holds})}
