from app.retrieval import Retriever

def test_delivery_policy_is_retrieved():
    r=Retriever()
    hits=r.search("customer says goods not received tracking delivery evidence",3)
    assert "goods_not_received" in [h.source_id for h in hits]

def test_service_not_provided_policy_is_retrieved():
    r=Retriever()
    hits=r.search("service was not provided evidence does not clearly confirm service completion",3)
    assert hits
    assert hits[0].source_id=="service_not_provided"


def test_irrelevant_query_returns_no_policy_above_threshold():
    r=Retriever()
    hits=r.search("quantum weather satellite orchid",3)
    assert hits==[]
