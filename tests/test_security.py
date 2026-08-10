from app.security import redact_sensitive

def test_redacts_pan_and_cvv():
    text="Card 4111 1111 1111 1111 CVV 123"
    out=redact_sensitive(text)
    assert "4111 1111 1111 1111" not in out
    assert "CVV 123" not in out
    assert out.endswith("[REDACTED_SECURITY_CODE]") or "[REDACTED_SECURITY_CODE]" in out
