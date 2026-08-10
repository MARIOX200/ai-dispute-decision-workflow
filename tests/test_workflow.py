import asyncio, tempfile
from pathlib import Path
from app.audit import AuditStore
from app.orchestrator import WorkflowEngine
from app.retrieval import Retriever
from app.schemas import CaseInput

def run(case):
    with tempfile.TemporaryDirectory() as td:
        return asyncio.run(WorkflowEngine(AuditStore(str(Path(td)/"x.db")),Retriever()).analyze(case))

def test_missing_delivery_evidence_goes_to_request_evidence():
    rec=run(CaseInput(case_id="T01",merchant="Demo",amount=100,currency="EUR",customer_claim="Goods not received",merchant_evidence="order confirmation only"))
    assert rec.recommended_action=="request_evidence"
    assert rec.needs_human_review is True

def test_duplicate_match_accepts_or_refunds():
    rec=run(CaseInput(case_id="T02",merchant="Demo",amount=20,currency="EUR",customer_claim="I was charged twice",transaction_signals={"duplicate_match":True}))
    assert rec.recommended_action=="accept_or_refund"

def test_ambiguous_service_not_provided_escalates_with_relevant_policy():
    rec=run(CaseInput(
        case_id="T03",
        merchant="Example Travel",
        amount=799,
        currency="EUR",
        customer_claim="Service was not provided as expected",
        merchant_evidence="Available evidence does not clearly confirm service completion",
        transaction_signals={"customer_contacted_support":True},
    ))
    assert rec.recommended_action=="escalate"
    assert rec.needs_human_review is True
    assert rec.sources
    assert rec.sources[0].source_id=="service_not_provided"
    assert "service completion evidence" in rec.missing_evidence
