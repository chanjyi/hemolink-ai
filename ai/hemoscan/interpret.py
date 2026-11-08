"""
HemoScan explanation + report assistant.

The language model only EXPLAINS findings the rules engine already produced from values the person
confirmed. It is never given raw PDF text and never decides anything. Without an API key (or on any
error) a template / curated FAQ answer is used instead.
"""
from __future__ import annotations

import re

from .. import llm
from .biomarkers import BY_KEY, CATALOG

EXPLAIN_SYSTEM = """You explain full blood count (FBC) results to members of the public in Malaysia, inside a blood donation app.
Rules you must follow:
- Only use the verified values and rule findings given to you. Do not add new findings or numbers.
- Say clearly that these are POSSIBLE associations, not a diagnosis. Never say the person "has" a condition.
- Do not recommend medicines, supplements, doses or treatments.
- If urgent values are listed, start by advising them to contact a doctor or clinic today.
- Plain English, short paragraphs, under 220 words. End with 2-3 questions they could ask their doctor.
"""

ASSIST_SYSTEM = """You answer questions about ONE full blood count report inside a blood donation app in Malaysia.
Rules you must follow:
- Use only the verified values and rule findings in the context. If something is not in the report, say so.
- Always distinguish possible associations from confirmed diagnoses. Never confirm or rule out a disease.
- Never recommend medicines, supplements, doses or treatments; say a doctor or pharmacist must advise.
- If urgent values exist, remind them to contact a doctor promptly.
- Under 150 words, plain English.
"""

TREATMENT_RE = re.compile(r"\b(dose|dosage|mg\b|how much (iron|vitamin|folate|b12)|should i (take|start|stop)|"
                          r"supplement|tablet|pill|medicine|medication|treat|cure|prescri)", re.I)
DIAGNOSIS_RE = re.compile(r"\b(do i have|have i got|mean i have|means i have|am i|is it|is this|could it be|confirm|diagnos)\b.*\b("
                          r"cancer|leuka?emia|lymphoma|thalass?a?emia|anaemia|anemia|dengue|disease|sick|ill|iron deficien)", re.I)

FAQ = [
    (("diagnosis", "mean i have", "does this mean", "confirm"),
     "No — HemoScan looks for number patterns that are often linked with certain conditions. Many things can cause the same "
     "pattern, so only a doctor who knows your symptoms and history can make a diagnosis, usually with extra tests."),
    (("range", "reference", "normal range", "different lab"),
     "Each lab sets its own reference range from its machines and population, so ranges differ slightly. HemoScan uses the "
     "range printed on your report; if none is printed it uses a typical adult range and tells you."),
    (("donate", "donation", "give blood"),
     "Blood banks check haemoglobin on the day before you donate. If your report shows low haemoglobin, wait until a doctor "
     "has reviewed it. Frequent donors can lose iron, so mention how often you donate."),
    (("repeat", "again", "follow up", "how often"),
     "Your doctor decides when to repeat the test. Out-of-range results are often re-checked after a few weeks, or sooner if "
     "you have symptoms."),
    (("ask", "doctor", "question"),
     "Good questions to ask: What could explain this pattern? Do I need more tests, such as ferritin? When should I repeat "
     "the blood count? Is it safe for me to keep donating blood?"),
    (("safe", "private", "privacy", "who can see"),
     "Your reports are private to your account — blood bank organizers and admins cannot see them. You can delete a report "
     "at any time."),
]


def _context(analysis: dict) -> str:
    lines = ["Verified values (lab or typical ranges):"]
    for x in analysis["results"]:
        if BY_KEY[x["key"]].percent:
            continue
        lines.append(f"- {x['name']}: {x['value']:g} {x['unit']} ({x['flag']}; range {x['ref_low']:g}-{x['ref_high']:g}, {x['ref_source']})")
    if analysis["urgent"]:
        lines.append("URGENT values: " + "; ".join(u["message"] for u in analysis["urgent"]))
    lines.append("Rule findings:")
    for f in analysis["findings"]:
        lines.append(f"- {f['title']} [{f['severity_label']}]. Triggered by: {'; '.join(f['why'])}. "
                     f"Possible associations: {', '.join(f['associations'])}. Usual next steps: {', '.join(f['next_steps'])}."
                     + (f" Note: {f['detail']}" if f.get("detail") and f["id"] != "urgent_values" else ""))
    if not analysis["findings"]:
        lines.append("- None: all recognised values are within range.")
    for t in analysis["trends"]:
        if t["note"]:
            lines.append(f"Trend: {t['note']} ({t['previous']:g} -> {t['current']:g} {t['unit']})")
    if analysis.get("donation"):
        lines.append("Donation: " + analysis["donation"]["message"])
        if analysis["donation"].get("frequent_donor_note"):
            lines.append(analysis["donation"]["frequent_donor_note"])
    return "\n".join(lines)


def template_explanation(analysis: dict, first_name: str) -> str:
    c = analysis["counts"]
    parts = []
    if analysis["urgent"]:
        parts.append("Important: some values on this report may need prompt attention. Please contact your doctor or clinic "
                     "today, and seek urgent care if you feel unwell.")
    out_of_range = c["low"] + c["high"]
    if out_of_range == 0:
        parts.append(f"Hi {first_name}, all the recognised values on this report are inside the reference ranges. That is "
                     "reassuring, but a blood count cannot rule out every condition — keep any symptoms in mind.")
    else:
        parts.append(f"Hi {first_name}, {out_of_range} value{'s are' if out_of_range > 1 else ' is'} outside the reference range "
                     f"({c['low']} low, {c['high']} high).")
    for f in [f for f in analysis["findings"] if f["id"] != "urgent_values" and f["severity"] != "info"][:3]:
        more = " (among other possible causes)" if len(f["associations"]) > 1 else ""
        parts.append(f"• {f['title']}. This pattern can be associated with: {f['associations'][0]}{more}. "
                     f"A usual next step is: {f['next_steps'][0]}.")
    notes = [t["note"] for t in analysis["trends"] if t["note"]]
    if notes:
        parts.append("Compared with your previous report: " + " ".join(notes))
    if analysis.get("donation") and not analysis["donation"]["ok"]:
        parts.append(analysis["donation"]["message"])
    parts.append("These are possible associations, not a diagnosis. Questions you could ask your doctor: What could explain "
                 "these results? Do I need further tests? When should I repeat the blood count?")
    return "\n\n".join(parts)


def explain(analysis: dict, first_name: str) -> tuple[str, bool]:
    text = llm.complete(EXPLAIN_SYSTEM, [{"role": "user", "content": f"First name: {first_name}\n\n{_context(analysis)}"}], 450)
    if text:
        return text.strip(), True
    return template_explanation(analysis, first_name), False


def doctor_questions(analysis: dict) -> list[str]:
    qs = []
    if analysis["urgent"]:
        qs.append("Some of my values were flagged as possibly urgent — do I need to be seen today?")
    for f in analysis["findings"]:
        if f["id"] in ("urgent_values", "mentzer", "rdw_supports_iron"):
            continue
        qs.append(f"My report shows “{f['title'].lower()}”. What could explain it in my case?")
        if f["next_steps"]:
            qs.append(f"Do you recommend this next step for me: {f['next_steps'][0]}?")
    if any(t["note"] for t in analysis["trends"]):
        qs.append("My results changed since my last test — is the trend important?")
    d = analysis.get("donation")
    if d and (not d["ok"] or d.get("frequent_donor_note")):
        qs.append("Is it safe for me to keep donating blood, and how long should I wait?")
    if not qs:
        qs.append("My results look within range — is there anything else you would like to check?")
    seen, out = set(), []
    for q in qs:
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out[:6]


def _glossary(question: str) -> str | None:
    q = question.lower()
    for b in CATALOG:
        if b.percent:
            continue
        short = b.name.split("(")[-1].rstrip(")").lower() if "(" in b.name else b.key
        names = {b.key, short, *b.aliases}
        if any(re.search(r"\b" + re.escape(n) + r"\b", q) for n in names if len(n) >= 2):
            return f"{b.name}: {b.explain}"
    return None


def answer(question: str, analysis: dict) -> dict:
    q = question.strip()
    if TREATMENT_RE.search(q):
        return {"answer": "I can't recommend medicines, supplements or doses — that needs a doctor or pharmacist who knows your "
                          "full history. I can explain what your values mean or suggest questions to ask them.",
                "source": "guardrail"}
    if DIAGNOSIS_RE.search(q):
        related = [f["title"] for f in analysis["findings"] if f["id"] != "urgent_values"]
        extra = (f" On this report the rules flagged: {'; '.join(related[:3])}. These are possible associations only."
                 if related else " On this report no pattern rules were triggered.")
        return {"answer": "A blood count alone can't confirm or rule out a disease — many conditions share the same pattern, "
                          "and a doctor needs your symptoms, history and usually more tests." + extra +
                          " Please discuss it with a doctor.", "source": "guardrail"}
    text = llm.complete(ASSIST_SYSTEM + "\n\nContext:\n" + _context(analysis), [{"role": "user", "content": q[:800]}], 300)
    if text:
        return {"answer": text.strip(), "source": "llm"}
    g = _glossary(q)
    ql = q.lower()
    for keys, ans in FAQ:
        if any(k in ql for k in keys):
            return {"answer": (g + "\n\n" + ans) if g else ans, "source": "faq"}
    if g:
        x = next((r for r in analysis["results"] if r["key"] in {b.key for b in CATALOG if g.startswith(b.name)}), None)
        if x:
            g += f" On this report it is {x['value']:g} {x['unit']} ({x['flag']}; range {x['ref_low']:g}–{x['ref_high']:g})."
        return {"answer": g, "source": "faq"}
    return {"answer": "I can explain any value on this report (try “What is MCV?”), what a flagged pattern means, why lab "
                      "ranges differ, or what to ask your doctor. I can't diagnose or recommend treatment.", "source": "faq"}
