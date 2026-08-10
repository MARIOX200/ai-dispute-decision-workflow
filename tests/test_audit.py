from pathlib import Path
import tempfile
from app.audit import AuditStore


def test_review_is_persisted_with_audit_fields():
    with tempfile.TemporaryDirectory() as td:
        store=AuditStore(str(Path(td)/"audit.db"))
        payload={"case_id":"T99","recommended_action":"escalate"}
        store.save_recommendation("T99","corr-1","escalate",0.49,payload,"REQUIRES_HUMAN_REVIEW")
        store.review("T99","represent","Mariusz Rek","Human override after evidence review")
        rec=store.get_recommendation("T99")
        assert rec is not None
        assert rec["status"]=="HUMAN_REVIEWED"
        assert rec["review"]["reviewed"] is True
        assert rec["review"]["agreement"] is False
        assert rec["review"]["comment"]=="Human override after evidence review"
        assert rec["review"]["reviewed_at"] is not None
