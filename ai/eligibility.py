"""
AI feature 3 (part A) — Eligibility rules engine.

The verdict is decided ONLY by these rules, never by the LLM; the LLM only explains it.

Rules checked on 8 Nov 2026 against (see SOURCES): Pusat Darah Negara's donor registration form (PDN 3/2014,
the screening questions and the Hb ≥ 12.5 g/dL check), PDN's FAQ / blog (age 17–70, weight, antibiotics,
dengue, surgery) and MOH JKN Johor (3-month interval, postpartum 6 months, chronic disease).
Where sources differed we used the official PDN form. Blood bank staff always make the final decision.
"""
from __future__ import annotations

from typing import Optional

from .schemas import Check, DonorHealth, EligibilityResult
from .util import add_days, days_between, format_date

SOURCES = [
    {"title": "PDN — Borang Pendaftaran Penderma Darah (PDN 3/2014)",
     "url": "https://pdn.gov.my/v2/images/dokumen/BORANG-PENDAFTARAN-PENDERMA-DARAH.pdf"},
    {"title": "PDN — FAQs Umum", "url": "https://pdn.gov.my/v2/index.php/maklumat-korporat/pengenalan/item/101-faqs-umum"},
    {"title": "PDN — Bahagian Perolehan Darah (blog: age, antibiotics, dengue, surgery)",
     "url": "https://pdn.gov.my/v2/index.php/perkhidmatan/bahagian-perolehan-darah/itemlist/category/1-blog?start=16"},
    {"title": "JKN Johor — Syarat-syarat penderma darah",
     "url": "https://jknjohor.moh.gov.my/hsi/syarat-syarat-penderma-darah-yang-layak/"},
    {"title": "The Rakyat Post — donation interval (citing PDN): men 3 months, women 4 months",
     "url": "https://www.therakyatpost.com/trpbm/kesihatan/2025/06/25/boleh-ke-derma-darah-terlalu-kerap-ini-penjelasannya/"},
]

RULES = {
    "sourceNote": "Based on Pusat Darah Negara (PDN) donor criteria, checked Nov 2026. A guide only — the doctor or "
    "screening staff at the drive make the final decision.",
    "checkedOn": "2026-11-08",
    "minAge": 17,                 # 17 needs written consent from a parent / guardian (PDN)
    "consentAge": 17,
    "firstTimeMaxAge": 60,        # first-time donors up to 60 (PDN)
    "maxAge": 65,                 # regular donors up to 65 without extra checks
    "absoluteMaxAge": 70,         # 66–70: regular donors with a yearly medical check-up or doctor's letter (PDN)
    "maxAgeLabel": "17–65 (first-time donors up to 60)",
    "minWeightKg": 45,            # "berat badan melebihi 45kg" (PDN FAQ)
    "hbMinGdl": 12.5,             # finger-prick check on the day; PDN form records "≥ 12.5 g/dL"
    "intervalDaysMale": 90,       # men every 3 months, max 4 a year
    "intervalDaysFemale": 120,    # women every 4 months, max 3 a year
    "wholeBloodIntervalDays": 90, # used when sex is not given (men's interval); women should add their sex in My Profile
    # triggerOn = the answer that triggers the rule
    # action: "defer" = wait N days, "staff" = staff check, "today" = fix today (e.g. eat first)
    "questions": [
        {"id": "feelingWell", "text": "Are you feeling well and healthy today?", "triggerOn": False, "action": "defer",
         "deferDays": 1, "reason": "Donors must feel well on the day of donation."},
        {"id": "sleep", "text": "Did you sleep at least 5 hours last night?", "triggerOn": False, "action": "defer",
         "deferDays": 1, "reason": "At least 5 hours of sleep lowers the chance of feeling faint."},
        {"id": "meal", "text": "Have you eaten a meal in the last 4 hours (not fasting)?", "triggerOn": False,
         "action": "today", "reason": "Don't donate while fasting — eat a meal first."},
        {"id": "fever", "text": "In the past week, have you had fever, flu, cough, a headache or migraine, or seen a doctor?",
         "triggerOn": True, "action": "defer", "deferDays": 7, "reason": "Wait until you have been well for a full week."},
        {"id": "antibiotics", "text": "Have you taken antibiotics in the last 2 weeks?", "triggerOn": True,
         "action": "defer", "deferDays": 14, "reason": "PDN asks donors to wait 2 weeks after the last antibiotic dose."},
        {"id": "dengue", "text": "Have you had dengue in the last 6 months?", "triggerOn": True, "action": "defer",
         "deferDays": 180, "reason": "Wait 6 months after full recovery from dengue."},
        {"id": "dental", "text": "Have you had dental treatment in the last 24 hours?", "triggerOn": True,
         "action": "defer", "deferDays": 1, "reason": "Wait 24 hours after dental treatment."},
        {"id": "tattoo", "text": "In the last 6 months, have you had a tattoo, body piercing, bekam (cupping) or acupuncture?",
         "triggerOn": True, "action": "defer", "deferDays": 180, "reason": "Skin procedures need a 6-month waiting period."},
        {"id": "surgery", "text": "In the last 6 months, have you had surgery, a blood transfusion or a needle-stick injury?",
         "triggerOn": True, "action": "defer", "deferDays": 180,
         "reason": "Wait 6 months after surgery, a transfusion or a needle-stick injury (staff may advise less after minor surgery)."},
        {"id": "vaccine", "text": "In the last 4 weeks, have you had a vaccine or a cosmetic injection (e.g. botox, filler)?",
         "triggerOn": True, "action": "staff", "reason": "Waiting time depends on the vaccine or injection — staff will check."},
        {"id": "alcohol", "text": "Have you been drunk in the last 24 hours?", "triggerOn": True, "action": "defer",
         "deferDays": 1, "reason": "Wait 24 hours after drinking alcohol."},
        {"id": "pregnant", "text": "(Women) Are you pregnant or breastfeeding, or did you give birth or miscarry in the last 6 months?",
         "triggerOn": True, "action": "defer", "deferDays": 180, "reason": "Your body needs time to rebuild iron stores."},
        {"id": "period", "text": "(Women) Are you having your period now?", "triggerOn": True, "action": "defer",
         "deferDays": 5, "reason": "Please come back after your period has ended."},
        {"id": "chronic", "text": "Do you have a long-term condition such as heart disease, cancer, diabetes, epilepsy, "
         "kidney disease, or hepatitis B/C?", "triggerOn": True, "action": "staff",
         "reason": "Some long-term conditions mean you cannot donate — the doctor at the drive will review yours."},
        {"id": "malaria", "text": "Have you ever had malaria, or travelled to a malaria-risk area in the last 12 months?",
         "triggerOn": True, "action": "staff", "reason": "Malaria history or recent travel needs a staff check."},
    ],
}


def interval_days(sex: Optional[str]) -> int:
    return RULES["intervalDaysFemale"] if sex == "female" else RULES["intervalDaysMale"]


VERDICT_LABEL = {
    "eligible": "You can donate",
    "eligible_after_meal": "You can donate after a meal",
    "deferred": "Not yet — please wait",
    "staff_check": "Please check with staff",
    "not_eligible": "Not eligible",
}


def next_eligible_by_interval(h: DonorHealth) -> Optional[str]:
    return add_days(h.donations[-1], interval_days(h.sex)) if h.donations else None


def evaluate(h: DonorHealth, today: str, answers: Optional[dict[str, bool]] = None) -> EligibilityResult:
    answers = answers or {}
    reasons: list[str] = []
    checks: list[Check] = []
    age = int(today[:4]) - h.birth_year
    eligible_from = today
    verdict = "eligible"

    first_time = not h.donations
    upper = RULES["firstTimeMaxAge"] if first_time else RULES["maxAge"]
    age_staff = False
    if age < RULES["minAge"]:
        age_ok, age_msg = False, f"Age {age} is under the minimum of {RULES['minAge']}."
    elif first_time and age > upper:
        age_ok, age_msg = False, f"First-time donors are accepted up to age {upper}."
    elif age > RULES["absoluteMaxAge"]:
        age_ok, age_msg = False, f"The upper age limit is {RULES['absoluteMaxAge']}."
    elif age > upper:  # regular donor aged 66–70
        age_ok, age_staff = True, True
        age_msg = (f"Regular donors aged {upper + 1}–{RULES['absoluteMaxAge']} need a yearly medical check-up "
                   "or a doctor's letter — staff will check.")
    elif age == RULES["consentAge"]:
        age_ok, age_staff = True, True
        age_msg = "At 17 you need written consent from a parent or guardian — bring the signed form."
    else:
        age_ok, age_msg = True, ""
    checks.append(Check(label="Age", ok=age_ok and not age_staff,
                        detail=f"{age} years (allowed {RULES['minAge']}–{upper}{'' if first_time else ', up to ' + str(RULES['absoluteMaxAge']) + ' with a check-up'})"))
    weight_ok = h.weight_kg >= RULES["minWeightKg"]
    checks.append(Check(label="Weight", ok=weight_ok, detail=f"{h.weight_kg:g} kg (minimum {RULES['minWeightKg']} kg)"))
    if age_msg:
        reasons.append(age_msg)
    if not weight_ok:
        reasons.append(f"Weight must be at least {RULES['minWeightKg']} kg.")
    if not age_ok or not weight_ok:
        verdict = "not_eligible"
    elif age_staff:
        verdict = "staff_check"

    last = h.donations[-1] if h.donations else None
    days_since_last = days_between(last, today) if last else None
    interval_date = next_eligible_by_interval(h)
    interval_ok = interval_date is None or interval_date <= today
    checks.append(Check(
        label="Time since last donation",
        ok=interval_ok,
        detail=f"{days_since_last} days (need {interval_days(h.sex)})" if last else "First-time donor",
    ))
    if not interval_ok and interval_date:
        gap = "4 months for women" if h.sex == "female" else "3 months for men" if h.sex == "male" else "3 months (4 for women)"
        reasons.append(f"Your body needs {interval_days(h.sex)} days between whole-blood donations ({gap}).")
        if verdict == "eligible":
            verdict = "deferred"
        eligible_from = max(eligible_from, interval_date)

    med_hold = h.medicine_hold_ongoing or bool(h.medicine_hold_until and h.medicine_hold_until > today)
    if med_hold:
        checks.append(Check(label="Medicines (HemoCare)", ok=False, detail=h.medicine_hold_reason or "Waiting period"))
        reasons.append(h.medicine_hold_reason or "A medicine in your list needs a waiting period.")
        if verdict == "eligible":
            verdict = "deferred"
        if h.medicine_hold_until and not h.medicine_hold_ongoing:
            eligible_from = max(eligible_from, h.medicine_hold_until)

    needs_meal = False
    for q in RULES["questions"]:
        if q["id"] not in answers:
            continue
        triggered = answers[q["id"]] == q["triggerOn"]
        checks.append(Check(label=q["text"], ok=not triggered, detail=q["reason"] if triggered else "OK"))
        if not triggered:
            continue
        reasons.append(q["reason"])
        if q["action"] == "staff":
            if verdict != "not_eligible":
                verdict = "staff_check"
        elif q["action"] == "defer":
            eligible_from = max(eligible_from, add_days(today, q.get("deferDays", 1)))
            if verdict == "eligible":
                verdict = "deferred"
        elif q["action"] == "today":
            needs_meal = True
    if verdict == "eligible" and needs_meal:
        verdict = "eligible_after_meal"

    return EligibilityResult(
        verdict=verdict,
        eligible_from=None if verdict in ("not_eligible", "staff_check") or (h.medicine_hold_ongoing and verdict == "deferred")
        else eligible_from,
        reasons=reasons,
        checks=checks,
        age=age,
        days_since_last=days_since_last,
    )


def is_basically_eligible(h: DonorHealth, today: str) -> bool:
    """Quick check used by matching: age, weight and donation interval only."""
    return evaluate(h, today).verdict == "eligible"


def template_explanation(r: EligibilityResult, first_name: str) -> str:
    """Plain-language explanation used when no LLM key is configured (demo mode)."""
    why = " ".join(r.reasons)
    if r.verdict == "eligible":
        return (f"Good news, {first_name}! Based on your answers you meet the basic requirements to donate today. "
                "Drink plenty of water and eat a proper meal before you go. Staff will do a quick health and "
                "haemoglobin check on site before the donation.")
    if r.verdict == "eligible_after_meal":
        return (f"You meet the basic requirements, {first_name}, but please eat a proper meal first. Donating on an "
                "empty stomach makes you more likely to feel dizzy. Staff will do a final health check on site.")
    if r.verdict == "deferred":
        when = format_date(r.eligible_from) if r.eligible_from else "a later date"
        return (f"Thanks for checking, {first_name}. You can't donate just yet: {why} You should be able to donate "
                f"from {when}. We'll remind you when the date comes.")
    if r.verdict == "staff_check":
        return (f"Thanks for being honest, {first_name}. One of your answers needs a quick review by blood bank staff "
                f"before you donate: {why} This doesn't mean you can't donate — just bring it up at registration or "
                "call the centre first.")
    return (f"Thank you for wanting to help, {first_name}. Right now you don't meet a basic requirement: {why} "
            "You can still help by sharing urgent requests with friends and family.")
