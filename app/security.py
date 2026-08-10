from __future__ import annotations
import re

PAN_RE = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
CVV_RE = re.compile(r"(?i)\b(?:cvv|cvc)\s*[:=]?\s*\d{3,4}\b")

def redact_sensitive(text: str) -> str:
    text = CVV_RE.sub("[REDACTED_SECURITY_CODE]", text)
    def repl(match: re.Match[str]) -> str:
        digits = re.sub(r"\D", "", match.group(0))
        return "**** **** **** " + digits[-4:] if len(digits) >= 4 else "[REDACTED_PAN]"
    return PAN_RE.sub(repl, text)
