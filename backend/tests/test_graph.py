def test_semantic_graph_admin(client, admin_headers):
    res = client.get("/api/v1/graph/semantic", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "edges" in data
    assert isinstance(data["nodes"], list)
    assert isinstance(data["edges"], list)
    if data["nodes"]:
        node = data["nodes"][0]
        assert "id" in node
        assert "label" in node
        assert "type" in node
        assert "document_count" in node
        assert "connection_count" in node
        assert "sentiment" in node
        assert "negative" in node["sentiment"]
        assert "neutral" in node["sentiment"]
        assert "positive" in node["sentiment"]
    if data["edges"]:
        edge = data["edges"][0]
        assert "id" in edge
        assert "source" in edge
        assert "target" in edge
        assert "weight" in edge

def test_semantic_node_documents_admin(client, admin_headers):
    sem_res = client.get("/api/v1/graph/semantic", headers=admin_headers)
    assert sem_res.status_code == 200
    nodes = sem_res.json()["nodes"]
    node_id = nodes[0]["id"] if nodes else "topic_nonexistent"
    res = client.get(f"/api/v1/graph/semantic/node/{node_id}/documents", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "documents" in data
    assert isinstance(data["documents"], list)

def test_lineage_graph_admin(client, admin_headers):
    res = client.get("/api/v1/graph/lineage", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "edges" in data
    assert isinstance(data["nodes"], list)
    assert isinstance(data["edges"], list)
    types_found = {n["type"] for n in data["nodes"]}
    assert "user" in types_found or len(data["nodes"]) == 0
    model_nodes = [n for n in data["nodes"] if n["type"] == "model"]
    for mn in model_nodes:
        assert "algorithm" in mn
        assert "feature_type" in mn
        assert "status" in mn
        assert "deployed" in mn
        assert "created_by" in mn

def test_graph_endpoints_forbidden_for_other_roles(
    client,
    analyst_headers,
    scientist_headers,
    manager_headers,
    reviewer_headers
):
    other_headers = [analyst_headers, scientist_headers, manager_headers, reviewer_headers]
    endpoints = [
        "/api/v1/graph/semantic",
        "/api/v1/graph/semantic/node/dummy_id/documents",
        "/api/v1/graph/lineage"
    ]
    for headers in other_headers:
        for ep in endpoints:
            res = client.get(ep, headers=headers)
            assert res.status_code == 403
            assert res.json()["error"]["code"] == "FORBIDDEN"

def test_semantic_graph_empty_or_unknown_dataset(client, admin_headers):
    res = client.get("/api/v1/graph/semantic?dataset_id=nonexistent-id", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["nodes"] == []
    assert data["edges"] == []
