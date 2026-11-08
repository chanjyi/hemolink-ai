"""
AI feature 3 (part B) — Donation assistant.

Guardrails run BEFORE the LLM: medical or off-topic questions get a safe fixed reply.
Without an LLM key, answers come from the FAQ below (keyword match).
"""
from __future__ import annotations

import re
from typing import Optional

from . import llm
from .eligibility import VERDICT_LABEL, template_explanation
from .schemas import AssistantReply, AssistantRequest, EligibilityResult, ExplainReply

SYSTEM = """You are HemoLink Assistant, a friendly helper inside a blood donation app in Malaysia.
Rules:
- Only talk about blood donation: eligibility in general terms, the donation process, preparation, after-care, booking, and how blood is used.
- Never diagnose, never give medication or treatment advice, never interpret test results. For any personal medical question say that blood bank staff or a doctor must decide.
- The app's rules engine decides eligibility; if the user's verdict is given in the context, explain it — do not change it.
- Keep answers under 120 words, plain English, warm tone. Use short bullet points only when listing steps.
- End eligibility-related answers with: "Blood bank staff make the final check on the day."
"""

MEDICAL = re.compile(
    r"\b(diagnos|prescri|dosage|dose|mg\b|medicine|medication|treat(ment)?|cure|symptom|cancer|hiv|test result|lab result|should i take)",
    re.I,
)
OFF_TOPIC = re.compile(r"\b(homework|bitcoin|stock price|politics|election|write (me )?(an? )?(essay|poem|code))\b", re.I)
ELIGIBILITY_Q = re.compile(r"can i (donate|give)|eligible|allowed to donate|this week", re.I)

MEDICAL_REPLY = (
    "I can't give medical advice or interpret personal health information. Please ask a doctor, or speak to the "
    "blood bank staff at registration — they'll check whether you can donate safely. I'm happy to explain how "
    "donation works or help you book a slot."
)
OFF_TOPIC_REPLY = (
    "I can only help with blood donation — eligibility basics, preparing, booking a slot, and after-care. "
    "What would you like to know?"
)

FAQ = [
    (["how long", "take", "duration", "minutes"],
     "The whole visit usually takes about 45–60 minutes: registration and a short health check, about 10 minutes "
     "for the donation itself, then 10–15 minutes resting with a drink and snack."),
    (["prepare", "before", "eat", "drink", "night"],
     "Sleep well, eat a proper meal in the 4 hours before, and drink plenty of water. Bring your IC. Wear a top "
     "with sleeves that roll up easily."),
    (["after", "aftercare", "dizzy", "exercise", "rest"],
     "Rest for 10–15 minutes and have the drink and snack offered. Drink extra water for the rest of the day and "
     "avoid heavy exercise or lifting for 24 hours. If you feel faint, lie down with your legs raised and tell staff."),
    (["how often", "again", "interval", "next", "wait", "months"],
     "For whole blood, this app uses a 90-day gap between donations (a demo setting — your blood bank confirms the "
     "exact rule). Your dashboard shows the date you can donate next."),
    (["o-", "o negative", "universal", "rare", "negative"],
     "O negative red cells can be given to patients of any blood type, so hospitals use them in emergencies before "
     "a patient's type is known. Few people are O negative, which is why stocks run low quickly."),
    (["safe", "hurt", "needle", "pain", "scared", "afraid"],
     "Donating is safe: every needle and bag is sterile and used only once. Most people feel a quick pinch when the "
     "needle goes in. Tell the staff if you're nervous — they help first-time donors all the time."),
    (["book", "slot", "appointment", "event", "drive", "register"],
     "Open Find Campaigns, choose an event, select an available time slot and confirm. Your appointment will appear "
     "under My Appointments."),
    (["cancel", "reschedule"],
     "Go to My Appointments and cancel a confirmed future appointment. You can then book a different available slot."),
    (["urgent", "emergency", "alert"],
     "When a blood bank is running low, HemoLink may alert a small group of matched donors. Urgent requests appear "
     "at the top of Notifications, where you tap “I can come” or “Can't make it”. For a medical emergency, contact emergency services; this demo cannot dispatch "
     "real blood products."),
    (["forecast", "prediction", "inventory", "shortage", "outlook"],
     "The shortage outlook projects each blood type's stock 7 days ahead from forecast donations and usage. In this "
     "prototype the stock and usage are simulated; the Donation Trends page (blood bank admins) uses official MOH "
     "donation counts once imported."),
    (["hemoscan", "blood test", "blood report", "fbc", "cbc", "full blood count", "lab report"],
     "HemoScan AI (in the donor menu) reads your full blood count PDF, lets you check the values, then shows what is out "
     "of range, possible patterns, trends over time and a summary for your doctor. It explains possible associations — "
     "it is not a diagnosis."),
    (["organizer", "organiser", "organise", "organize", "host a drive", "run a drive"],
     "Community groups such as universities, companies and NGOs can run blood drives. Sign up as a donor, then ask the "
     "blood bank to approve your account as a drive organizer — you can then create campaigns and check donors in."),
    (["eligible", "can i donate", "allowed", "qualify", "age", "weight"],
     "Use the Eligibility Check page: it asks a few quick questions and tells you whether you can donate now or "
     "from which date. Blood bank staff make the final check on the day."),
    (["used", "where", "who", "patients", "go"],
     "Donated blood is tested and split into red cells, plasma and platelets, so one donation can help more than "
     "one patient — for example people in surgery, accident victims, new mothers and patients with blood disorders."),
]

FAQ_DEFAULT = (
    "I can help with eligibility basics, preparing for a donation, booking a slot, urgent alerts, after-care and why "
    "blood types matter. Try asking “How should I prepare?” or “How often can I donate?”"
)


def guard(question: str) -> Optional[str]:
    if MEDICAL.search(question):
        return MEDICAL_REPLY
    if OFF_TOPIC.search(question):
        return OFF_TOPIC_REPLY
    return None


def faq_answer(question: str) -> str:
    q = question.lower()
    best_score, best = 0, FAQ_DEFAULT
    for keys, answer in FAQ:
        score = sum(len(k) for k in keys if k in q)
        if score > best_score:
            best_score, best = score, answer
    return best


def reply(req: AssistantRequest) -> AssistantReply:
    messages = [{"role": m.role, "content": m.content[:1000]} for m in req.messages[-10:]]
    last = messages[-1]["content"] if messages else ""

    blocked = guard(last)
    if blocked:
        return AssistantReply(reply=blocked, source="guardrail")

    answer = llm.complete(SYSTEM + req.context, messages, 350)
    if answer:
        return AssistantReply(reply=answer, source="llm")

    if req.eligibility_summary and ELIGIBILITY_Q.search(last):
        return AssistantReply(
            reply=f"{req.eligibility_summary} Do the 1-minute eligibility check for today's health questions, then "
            "book a slot under \"Find a drive\". Blood bank staff make the final check on the day.",
            source="faq",
        )
    return AssistantReply(reply=faq_answer(last), source="faq")


def explain(result: EligibilityResult, first_name: str) -> ExplainReply:
    text = llm.complete(
        "You explain blood donation eligibility results to donors in Malaysia. The verdict below was decided by a "
        "rules engine and is FINAL — explain it, never change it, never add medical advice. Under 90 words, warm "
        'and clear. End with: "Blood bank staff make the final check on the day."',
        [{
            "role": "user",
            "content": f"Donor first name: {first_name}\nVerdict: {VERDICT_LABEL[result.verdict]}\n"
            f"Eligible from: {result.eligible_from or 'n/a'}\nReasons: {' | '.join(result.reasons) or 'none'}\n"
            "Write the explanation.",
        }],
        250,
    )
    if text:
        return ExplainReply(explanation=text, used_llm=True)
    return ExplainReply(explanation=template_explanation(result, first_name), used_llm=False)
