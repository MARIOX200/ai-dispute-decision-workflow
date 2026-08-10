# Architecture and role alignment

## Why this project exists

PModern applied AI engineering requires production-grade workflows, orchestration, retrieval, model-behaviour evaluation, APIs, reliability and auditable operation. This project turns those concerns into executable interfaces rather than a slide-only concept.

## Boundaries

- `app/main.py`: API boundary for internal systems.
- `app/orchestrator.py`: lifecycle ownership and decision routing.
- `app/retrieval.py`: approved-source retrieval.
- `app/providers.py`: AI/decision provider with retry and fallback.
- `app/security.py`: pre-processing controls for sensitive data.
- `app/audit.py`: decision and human-override traceability.
- `app/eval/run_eval.py`: structured evaluation and outcome metrics.

## Reliability patterns

1. Every case receives a correlation ID.
2. Provider calls retry before fallback.
3. Missing evidence and low confidence route to Human-in-the-Loop.
4. Recommendations persist before human decision.
5. Human override is recorded separately from AI output.
6. The workflow can run without external AI availability.

## Data-engineering collaboration contract

A production version would retain the Pydantic event and response schemas while moving persistence/eventing to managed services. This makes shared standards, schemas, data lineage, security and CI/CD explicit collaboration points rather than hidden implementation details.
