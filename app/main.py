from __future__ import annotations
from fastapi import FastAPI, HTTPException
from .audit import AuditStore
from .config import settings
from .logging_utils import configure_logging
from .orchestrator import WorkflowEngine
from .retrieval import Retriever
from .schemas import AIRecommendation, CaseInput, HumanReview, ReviewResult

configure_logging(settings.log_level)
store=AuditStore(settings.database_path)
retriever=Retriever()
engine=WorkflowEngine(store,retriever)
app=FastAPI(title="AI Dispute Decision Workflow",version="0.2.0")

@app.get("/health")
def health(): return {"status":"ok","provider":engine.primary.name,"version":"0.2.0","min_retrieval_score":settings.min_retrieval_score}

@app.post("/v1/cases/analyze",response_model=AIRecommendation)
async def analyze(case: CaseInput):
    return await engine.analyze(case)

@app.post("/v1/cases/{case_id}/review",response_model=ReviewResult)
def review(case_id: str, review: HumanReview):
    rec=store.get_recommendation(case_id)
    if not rec: raise HTTPException(status_code=404,detail="case not found")
    store.review(case_id,review.decision,review.reviewer,review.comment)
    store.event(case_id,rec["correlation_id"],"human_review_completed",{
        "ai_action":rec["action"],
        "human_action":review.decision,
        "agreement":rec["action"]==review.decision,
        "reviewer":review.reviewer,
        "comment":review.comment,
    })
    return ReviewResult(case_id=case_id,ai_action=rec["action"],human_action=review.decision,agreement=rec["action"]==review.decision,reviewer=review.reviewer)

@app.get("/v1/cases/{case_id}")
def get_case(case_id: str):
    rec=store.get_recommendation(case_id)
    if not rec: raise HTTPException(status_code=404,detail="case not found")
    return rec
