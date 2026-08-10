from __future__ import annotations
import asyncio, json
import httpx
from .schemas import Action, CaseInput, RetrievalHit

class ProviderError(RuntimeError): pass

class BaseProvider:
    name = "base"
    async def decide(self, case: CaseInput, hits: list[RetrievalHit]) -> dict: raise NotImplementedError

class LocalDecisionProvider(BaseProvider):
    name = "local-deterministic"
    async def decide(self, case: CaseInput, hits: list[RetrievalHit]) -> dict:
        text=(case.customer_claim+" "+case.merchant_evidence).lower()
        evidence=case.merchant_evidence.lower()
        signals=case.transaction_signals
        missing=[]
        if not case.merchant_evidence.strip(): missing.append("merchant evidence")
        if "not received" in text or "not delivered" in text:
            if any(w in evidence for w in ["delivery", "tracking", "signed", "proof of delivery"]):
                action: Action="represent"; confidence=.86
            else:
                action="request_evidence"; confidence=.82; missing.append("proof of delivery")
        elif any(w in text for w in ["duplicate", "charged twice", "two charges"]):
            if signals.get("duplicate_match") is True:
                action="accept_or_refund"; confidence=.91
            else:
                action="escalate"; confidence=.62
        elif any(w in text for w in ["fraud", "not mine", "unauthorised", "unauthorized"]):
            if signals.get("sca") is True or signals.get("3ds") is True:
                action="represent"; confidence=.77
            else:
                action="escalate"; confidence=.58
        elif any(w in text for w in ["cancel", "refund"]):
            negative_refund = any(w in evidence for w in ["no refund", "refund not issued", "not refunded"])
            if (not negative_refund) and any(w in evidence for w in ["refund issued", "credited", "refund confirmation included", "refund confirmation attached"]):
                action="represent"; confidence=.79
            else:
                action="accept_or_refund"; confidence=.73
        elif any(w in text for w in ["service was not provided", "service not provided", "service was not delivered", "service not delivered", "service completion"]):
            ambiguous = any(w in evidence for w in ["does not clearly confirm", "not confirmed", "no confirmation", "unclear", "incomplete", "contradictory"])
            positive = any(w in evidence for w in ["service completed", "completion confirmation", "attendance confirmed", "access log", "signed acknowledgement"])
            if positive and not ambiguous:
                action="represent"; confidence=.82
            else:
                action="escalate"; confidence=.54; missing.append("service completion evidence")
        else:
            action="escalate"; confidence=.49
        rationale=f"Decision derived from case signals and retrieved internal policy. Top source: {hits[0].title if hits else 'none'}; retrieval {'matched' if hits else 'below relevance threshold'}."
        return {"recommended_action":action,"confidence":confidence,"rationale":rationale,"missing_evidence":sorted(set(missing))}

class OpenAIProvider(BaseProvider):
    name = "openai"
    def __init__(self, api_key: str, model: str): self.api_key=api_key; self.model=model
    async def decide(self, case: CaseInput, hits: list[RetrievalHit]) -> dict:
        system=("You are a cautious payment-dispute decision-support agent. Return JSON only with keys: "
                "recommended_action, confidence, rationale, missing_evidence. Allowed actions: represent, request_evidence, accept_or_refund, escalate. "
                "Do not make unsupported claims. Escalate ambiguity. The final decision belongs to a human reviewer.")
        context="\n\n".join(h.excerpt for h in hits)
        user=json.dumps({"case":case.model_dump(),"retrieved_policy":context}, ensure_ascii=False)
        body={"model":self.model,"input":[{"role":"system","content":system},{"role":"user","content":user}]}
        headers={"Authorization":f"Bearer {self.api_key}","Content-Type":"application/json"}
        async with httpx.AsyncClient(timeout=30) as client:
            r=await client.post("https://api.openai.com/v1/responses",json=body,headers=headers)
        if r.status_code>=300: raise ProviderError(f"OpenAI HTTP {r.status_code}")
        data=r.json(); text=data.get("output_text")
        if not text:
            chunks=[]
            for item in data.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") in {"output_text", "text"} and content.get("text"):
                        chunks.append(content["text"])
            text="\n".join(chunks)
        if not text: raise ProviderError("No text returned by provider")
        text=text.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(text)

async def with_retry(call, attempts: int = 2, delay: float = 0.05):
    last=None
    for _ in range(attempts):
        try: return await call()
        except Exception as exc:
            last=exc; await asyncio.sleep(delay)
    raise ProviderError(str(last))
