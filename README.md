# AI Dispute Decision Workflow

**Production-oriented AI engineering portfolio project for payment dispute operations**

A production-oriented demonstration of an auditable AI workflow for payment-dispute operations. It is intentionally designed around the engineering concerns in the role: agents/decision logic, retrieval, Human-in-the-Loop, retries, fallbacks, APIs, observability, evaluation, governance and measurable outcomes.

> Status: runnable portfolio engineering demonstrator. It is not claimed as a production deployment in a bank, card scheme or payment processor. The included policies and cases are synthetic internal-demo material.

## What it demonstrates

- FastAPI service with typed request/response contracts.
- Retrieval pipeline over an approved knowledge base (TF-IDF offline implementation).
- Provider abstraction: deterministic local provider by default; optional OpenAI Responses API adapter.
- Orchestration with retries and deterministic fallback.
- Human-in-the-Loop review endpoint and audit persistence in SQLite.
- Sensitive-data redaction before persistence/prompting.
- JSON structured logging and correlation IDs.
- Evaluation harness tracking decision accuracy, retrieval hit-rate, automation resolution rate, pipeline latency and estimated time saved.
- Docker / Docker Compose and GitHub Actions CI.
- Unit tests for workflow behaviour, retrieval and data-safety controls.

## Architecture

```text
Case / internal-system event
          |
          v
   FastAPI contract
          |
          v
Sensitive-data redaction
          |
          v
 Retrieval pipeline --------> Approved knowledge base
          |
          v
 Primary AI provider
     | retry x2
     +------ failure ------> deterministic fallback
          |
          v
Decision + confidence + evidence gaps
          |
          +---- low confidence / missing evidence ----> Human review
          |
          v
 Audit store + structured logs + evaluation feedback
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q
python -m app.eval.run_eval --output artifacts/eval_results.json
uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000/docs`.

Docker:

```bash
docker compose up --build
```

## Example API call

```bash
curl -X POST http://127.0.0.1:8000/v1/cases/analyze \
  -H 'Content-Type: application/json' \
  -d '{
    "case_id":"DEMO-001",
    "merchant":"Example Store",
    "amount":249.90,
    "currency":"EUR",
    "customer_claim":"Goods not received",
    "merchant_evidence":"Carrier tracking shows delivered and signed proof of delivery"
  }'
```

## Optional live LLM mode

The repository runs without secrets. To test the optional provider adapter, create `.env` or export:

```bash
export AI_PROVIDER=openai
export OPENAI_API_KEY=...
export OPENAI_MODEL=gpt-5-mini
```

The local deterministic provider remains the safe fallback.

## Engineering trade-offs

This repository deliberately uses a local TF-IDF retriever and SQLite to remain self-contained and reproducible. In an enterprise deployment these boundaries can be replaced with Azure AI Search / vector search, managed databases, enterprise eventing and managed observability without changing the API and orchestration contracts.

## Evaluation

Run:

```bash
python -m app.eval.run_eval
```

The dataset is synthetic and intended to make failure modes visible. `EVALUATION.md` records an actual v1 failure analysis and v2 regression improvement. Metrics are portfolio evidence only, not production performance claims.

## Production hardening backlog

- Managed queue/event bus and idempotent workers.
- Distributed tracing / OpenTelemetry.
- OAuth2/OIDC and RBAC.
- Managed secrets and key rotation.
- Real vector store / reranking and source-version controls.
- Canary releases, prompt/model registry and rollback.
- Online feedback loop with labelled human overrides.
- Load, chaos and security testing.

## v0.2.0 hardening

- adds a minimum retrieval relevance threshold and a safe no-policy fallback,
- adds a Service Not Provided demo policy,
- persists Human-in-the-Loop review details, agreement, comment and timestamp,
- adds lifecycle statuses (`AI_ANALYSED`, `REQUIRES_HUMAN_REVIEW`, `HUMAN_REVIEWED`),
- records retrieval scores and review events in the audit trail.
