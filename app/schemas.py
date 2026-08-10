from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

Action = Literal["represent", "request_evidence", "accept_or_refund", "escalate"]

class CaseInput(BaseModel):
    case_id: str = Field(min_length=3, max_length=80)
    merchant: str
    amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    customer_claim: str
    merchant_evidence: str = ""
    transaction_signals: dict[str, str | bool | float] = Field(default_factory=dict)

class RetrievalHit(BaseModel):
    source_id: str
    title: str
    score: float
    excerpt: str

class AIRecommendation(BaseModel):
    case_id: str
    recommended_action: Action
    confidence: float = Field(ge=0, le=1)
    rationale: str
    missing_evidence: list[str]
    sources: list[RetrievalHit]
    needs_human_review: bool
    used_fallback: bool = False
    model_provider: str
    correlation_id: str

class HumanReview(BaseModel):
    reviewer: str
    decision: Action
    comment: str = ""

class ReviewResult(BaseModel):
    case_id: str
    ai_action: Action
    human_action: Action
    agreement: bool
    reviewer: str
