from __future__ import annotations
import logging, uuid
from .audit import AuditStore
from .config import settings
from .providers import LocalDecisionProvider, OpenAIProvider, with_retry
from .retrieval import Retriever
from .schemas import AIRecommendation, CaseInput
from .security import redact_sensitive

log=logging.getLogger("orchestrator")

class WorkflowEngine:
    def __init__(self, store: AuditStore, retriever: Retriever):
        self.store=store; self.retriever=retriever
        self.local=LocalDecisionProvider()
        self.primary=(OpenAIProvider(settings.openai_api_key, settings.openai_model)
                      if settings.ai_provider=="openai" and settings.openai_api_key else self.local)

    async def analyze(self, case: CaseInput) -> AIRecommendation:
        correlation_id=str(uuid.uuid4())
        safe=case.model_copy(update={
            "customer_claim":redact_sensitive(case.customer_claim),
            "merchant_evidence":redact_sensitive(case.merchant_evidence),
        })
        self.store.event(case.case_id,correlation_id,"case_received",{"merchant":case.merchant,"amount":case.amount,"currency":case.currency})
        query=f"{safe.customer_claim} {safe.merchant_evidence} {safe.transaction_signals}"
        hits=self.retriever.search(query,k=3)
        self.store.event(case.case_id,correlation_id,"retrieval_completed",{
            "sources":[h.source_id for h in hits],
            "scores":[h.score for h in hits],
            "threshold":settings.min_retrieval_score,
            "status":"matched" if hits else "below_relevance_threshold",
        })
        used_fallback=False
        if not hits:
            result={
                "recommended_action":"escalate",
                "confidence":.35,
                "rationale":"No internal policy met the configured retrieval relevance threshold; escalated to human review.",
                "missing_evidence":["relevant policy or additional case evidence"],
            }
        else:
            try:
                result=await with_retry(lambda: self.primary.decide(safe,hits),attempts=2)
            except Exception as exc:
                used_fallback=True
                self.store.event(case.case_id,correlation_id,"provider_failure",{"error":type(exc).__name__})
                result=await self.local.decide(safe,hits)
        confidence=float(result["confidence"])
        needs_review=confidence<0.75 or result["recommended_action"]=="escalate" or bool(result.get("missing_evidence"))
        rec=AIRecommendation(
            case_id=case.case_id,
            recommended_action=result["recommended_action"],
            confidence=confidence,
            rationale=result["rationale"],
            missing_evidence=result.get("missing_evidence",[]),
            sources=hits,
            needs_human_review=needs_review,
            used_fallback=used_fallback,
            model_provider=self.primary.name if not used_fallback else self.local.name,
            correlation_id=correlation_id,
        )
        status="REQUIRES_HUMAN_REVIEW" if rec.needs_human_review else "AI_ANALYSED"
        self.store.save_recommendation(case.case_id,correlation_id,rec.recommended_action,rec.confidence,rec.model_dump(),status)
        self.store.event(case.case_id,correlation_id,"recommendation_created",{"action":rec.recommended_action,"confidence":rec.confidence,"needs_human_review":rec.needs_human_review,"status":status})
        log.info("recommendation_created",extra={"correlation_id":correlation_id,"case_id":case.case_id,"event_type":"recommendation_created"})
        return rec
