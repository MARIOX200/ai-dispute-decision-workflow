# Evaluation and feedback loop

The evaluation set is synthetic and deliberately small. It is used as a regression suite, not as a claim of real-world model performance.

## First run (v1)

- 30 synthetic cases
- decision accuracy: **93.33%**
- retrieval hit rate@3: **73.33%**

Failure review found two concrete engineering issues:

1. The duplicate-processing policy did not include the user phrase **"charged twice"**, so lexical retrieval missed the relevant source.
2. Refund evidence logic treated **"no refund confirmation"** as if positive confirmation existed - a classic negation failure.

## Regression run (v2)

After extending retrieval vocabulary and making refund evidence negation-aware:

- decision accuracy: **100% on the 30-case regression set**
- retrieval hit rate@3: **100%**
- automation resolution rate: **40%** (remaining cases require human review)
- modeled time saving: **62.5%** (8 minute manual baseline vs 3 minute assisted assumption)

The important result is not the perfect regression score. The evidence is the feedback loop: measure -> inspect failures -> change retrieval/logic -> rerun tests -> retain the case as a regression test. A larger production system would add a hold-out set, online human-overrides, prompt/model versioning and statistical monitoring.
