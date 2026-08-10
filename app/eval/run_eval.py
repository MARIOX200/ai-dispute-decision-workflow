from __future__ import annotations
import argparse, asyncio, json, os, tempfile, time
from pathlib import Path
from app.audit import AuditStore
from app.orchestrator import WorkflowEngine
from app.retrieval import Retriever
from app.schemas import CaseInput

DATA=Path("data/eval_cases.json")

async def run():
    rows=json.loads(DATA.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as td:
        engine=WorkflowEngine(AuditStore(str(Path(td)/"eval.db")),Retriever())
        correct=0; auto_resolved=0; latencies=[]; source_hits=0
        outputs=[]
        for row in rows:
            case=CaseInput(**row["case"])
            t=time.perf_counter(); rec=await engine.analyze(case); latencies.append(time.perf_counter()-t)
            ok=rec.recommended_action==row["expected_action"]
            correct+=int(ok)
            auto_resolved+=int(not rec.needs_human_review)
            expected_source=row.get("expected_source")
            source_hits+=int(expected_source in [h.source_id for h in rec.sources] if expected_source else True)
            outputs.append({"case_id":case.case_id,"expected":row["expected_action"],"actual":rec.recommended_action,"correct":ok,"confidence":rec.confidence,"needs_human_review":rec.needs_human_review,"sources":[h.source_id for h in rec.sources]})
    n=len(rows)
    return {
      "cases":n,
      "decision_accuracy":round(correct/n,4),
      "retrieval_hit_rate_at_3":round(source_hits/n,4),
      "automation_resolution_rate":round(auto_resolved/n,4),
      "median_pipeline_latency_ms":round(sorted(latencies)[n//2]*1000,2),
      "estimated_manual_minutes_per_case":8.0,
      "estimated_assisted_minutes_per_case":3.0,
      "estimated_time_saved_percent":62.5,
      "note":"Synthetic evaluation dataset and deterministic local provider; metrics are portfolio evidence, not production business results.",
      "outputs":outputs,
    }

def main():
    p=argparse.ArgumentParser(); p.add_argument("--output",default="artifacts/eval_results.json"); args=p.parse_args()
    result=asyncio.run(run()); Path(args.output).parent.mkdir(parents=True,exist_ok=True); Path(args.output).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="outputs"},indent=2))

if __name__=="__main__": main()
