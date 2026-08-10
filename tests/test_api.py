import os, tempfile
from fastapi.testclient import TestClient

def test_health_and_analyze(monkeypatch):
    # import app after setting a temporary DB path
    with tempfile.TemporaryDirectory() as td:
        monkeypatch.setenv("DATABASE_PATH", td+"/api.db")
        import importlib
        import app.config as config
        importlib.reload(config)
        import app.main as main
        importlib.reload(main)
        client=TestClient(main.app)
        assert client.get("/health").status_code==200
        r=client.post("/v1/cases/analyze",json={
            "case_id":"API-001","merchant":"Demo","amount":42.0,"currency":"EUR",
            "customer_claim":"Goods not received","merchant_evidence":"order confirmation only"})
        assert r.status_code==200
        assert r.json()["recommended_action"]=="request_evidence"
