"""
Data shapes shared with the Next.js website.

Python code uses snake_case; JSON on the wire uses camelCase (same as the TypeScript types
in src/lib/types.ts), handled automatically by the alias generator.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

BloodType = Literal["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]
BLOOD_TYPES: list[str] = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]


class Model(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")


# ---------------- core records ----------------


class Profile(Model):
    id: str
    role: str
    name: str
    area: str = ""
    state: str = ""
    lat: float
    lng: float
    centre_id: Optional[str] = None


class LastCheck(Model):
    at: str
    answers: dict[str, bool]


class DonorHealth(Model):
    donor_id: str
    blood_type: BloodType
    birth_year: int
    weight_kg: float
    sex: Optional[Literal["female", "male"]] = None
    donations: list[str] = Field(default_factory=list)
    no_shows: int = 0
    last_check: Optional[LastCheck] = None
    # HemoCare: a medicine with a donation waiting period (placeholder rules, confirmed by screening staff)
    medicine_hold_until: Optional[str] = None
    medicine_hold_ongoing: bool = False
    medicine_hold_reason: Optional[str] = None


class Centre(Model):
    id: str
    name: str
    area: str = ""
    state: str = ""
    lat: float
    lng: float


class Alert(Model):
    id: str
    request_id: str
    donor_id: str
    score: float = 0
    reasons: list[str] = Field(default_factory=list)
    sent_at: str
    response: Optional[Literal["yes", "no"]] = None


class UrgentRequest(Model):
    id: str
    centre_id: str
    blood_type: BloodType
    units: int
    needed_by: str
    note: str = ""
    status: str = "open"
    created_at: str = ""


class DayRecord(Model):
    date: str
    collected: float
    used: float


# ---------------- forecast ----------------


class ForecastInput(Model):
    blood_type: BloodType
    records: list[DayRecord]
    current_units: float
    with_backtest: bool = False


class ForecastRequest(Model):
    today: str
    items: list[ForecastInput]


class Backtest(Model):
    mae: float
    baseline_mae: float
    mean_actual: float
    days: int


class ForecastPoint(Model):
    date: str
    collected: float
    used: float
    stock: int


class StockPoint(Model):
    date: str
    stock: int


class TypeForecast(Model):
    blood_type: BloodType
    current_units: float
    avg_daily_use: float
    days_of_supply: float
    safety_units: int
    points: list[ForecastPoint]
    days_until_unsafe: Optional[int]
    days_until_empty: Optional[int]
    status: Literal["red", "amber", "green"]
    supply_trend_pct: int
    backtest: Backtest
    recent: list[StockPoint]


# ---------------- eligibility ----------------


class EligibilityRequest(Model):
    today: str
    health: DonorHealth
    answers: dict[str, bool] = Field(default_factory=dict)


class EligibilityBatchRequest(Model):
    today: str
    health: list[DonorHealth]


class Check(Model):
    label: str
    ok: bool
    detail: str


class EligibilityResult(Model):
    verdict: Literal["eligible", "eligible_after_meal", "deferred", "staff_check", "not_eligible"]
    eligible_from: Optional[str]
    reasons: list[str]
    checks: list[Check]
    age: int
    days_since_last: Optional[int]


# ---------------- matching ----------------


class MatchRequest(Model):
    today: str
    request: UrgentRequest
    centre: Centre
    profiles: list[Profile]
    health: list[DonorHealth]
    alerts: list[Alert]
    margin: float = 1.5
    max_alerts: int = 40


class MatchCandidate(Model):
    donor_id: str
    km: float
    score: int
    p_yes: float
    response_rate: int
    alerts_received: int
    reasons: list[str]
    selected: bool


class Excluded(Model):
    not_compatible: int = 0
    not_eligible: int = 0
    too_far: int = 0
    already_alerted: int = 0


class MatchResult(Model):
    candidates: list[MatchCandidate]
    selected_count: int
    expected_yes: float
    excluded: Excluded


# ---------------- return prediction ----------------


class ReturnRequest(Model):
    today: str
    profiles: list[Profile]
    health: list[DonorHealth]
    centres: list[Centre]


class ReturnModelInfo(Model):
    weights: list[float]
    bias: float


class TrainReport(Model):
    model: ReturnModelInfo
    train_size: int
    test_size: int
    accuracy: float
    auc: float
    base_rate: float
    feature_names: list[str]


class ReturnScore(Model):
    donor_id: str
    p_return: float
    days_since_last: int
    top_factor: str


class ReturnResponse(Model):
    report: TrainReport
    scores: list[ReturnScore]


# ---------------- assistant ----------------


class ChatMessage(Model):
    role: Literal["user", "assistant"]
    content: str


class AssistantRequest(Model):
    messages: list[ChatMessage]
    context: str = ""
    # rules-engine status for a personalised fallback answer (demo mode)
    eligibility_summary: Optional[str] = None


class AssistantReply(Model):
    reply: str
    source: Literal["llm", "faq", "guardrail"]


class ExplainRequest(Model):
    first_name: str
    result: EligibilityResult


class ExplainReply(Model):
    explanation: str
    used_llm: bool
