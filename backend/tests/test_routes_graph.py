"""Unit tests for graph API endpoints:
  GET  /papers/{id}/graph
  GET  /papers/{id}/node/{nid}
  POST /graph/expand
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import make_supabase_mock


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

PAPER_ID = "paper-uuid-111"
NODE_ID_A = "node-uuid-aaa"
NODE_ID_B = "node-uuid-bbb"
EDGE_ID = "edge-uuid-eee"

_BASE_NODE = {
    "paper_id": PAPER_ID,
    "simplified_explanation": None,
    "advantages": [],
    "limitations": [],
    "key_equations": [],
    "source_text": None,
    "section_name": None,
    "section_number": None,
    "page_number": None,
    "label": None,
}

NODE_A = {
    **_BASE_NODE,
    "id": NODE_ID_A,
    "type": "method",
    "title": "Attention",
    "description": "Self-attention mechanism",
}

NODE_B = {
    **_BASE_NODE,
    "id": NODE_ID_B,
    "type": "concept",
    "title": "Transformer",
    "description": "Encoder-decoder architecture",
}

EDGE_AB = {
    "id": EDGE_ID,
    "paper_id": PAPER_ID,
    "source_node_id": NODE_ID_A,
    "target_node_id": NODE_ID_B,
    "relationship_type": "BUILDS_ON",
}


# ---------------------------------------------------------------------------
# GET /papers/{paper_id}/graph
# ---------------------------------------------------------------------------

class TestGetGraph:
    def test_paper_not_found_returns_404(self, client):
        response = client.get(f"/papers/bad-id/graph")
        assert response.status_code == 404

    def test_returns_nodes_and_edges_in_react_flow_format(self):
        execute_results = [
            MagicMock(data=[{"id": PAPER_ID}]),   # paper existence check
            MagicMock(data=[NODE_A]),              # nodes query
            MagicMock(data=[EDGE_AB]),             # edges query
        ]
        db_mock, execute_mock = make_supabase_mock()
        execute_mock.side_effect = execute_results

        with patch("app.db.postgres_client._client", db_mock):
            response = TestClient(app).get(f"/papers/{PAPER_ID}/graph")

        assert response.status_code == 200
        body = response.json()
        assert body["nodes"][0]["id"] == NODE_ID_A
        assert body["edges"][0]["source"] == NODE_ID_A
        assert body["edges"][0]["target"] == NODE_ID_B
        assert body["edges"][0]["label"] == "BUILDS_ON"

    def test_empty_graph_returns_empty_lists(self):
        execute_results = [
            MagicMock(data=[{"id": PAPER_ID}]),
            MagicMock(data=[]),
            MagicMock(data=[]),
        ]
        db_mock, execute_mock = make_supabase_mock()
        execute_mock.side_effect = execute_results

        with patch("app.db.postgres_client._client", db_mock):
            response = TestClient(app).get(f"/papers/{PAPER_ID}/graph")

        assert response.status_code == 200
        assert response.json() == {"nodes": [], "edges": []}

    def test_node_data_contains_all_fields(self):
        execute_results = [
            MagicMock(data=[{"id": PAPER_ID}]),
            MagicMock(data=[NODE_A]),
            MagicMock(data=[]),
        ]
        db_mock, execute_mock = make_supabase_mock()
        execute_mock.side_effect = execute_results

        with patch("app.db.postgres_client._client", db_mock):
            response = TestClient(app).get(f"/papers/{PAPER_ID}/graph")

        node = response.json()["nodes"][0]
        expected_keys = {
            "title", "description", "type", "simplified_explanation",
            "advantages", "limitations", "key_equations", "source_text",
            "section_name", "section_number", "page_number", "label",
        }
        assert expected_keys.issubset(node["data"].keys())

    def test_grid_position_assigned_to_nodes(self):
        execute_results = [
            MagicMock(data=[{"id": PAPER_ID}]),
            MagicMock(data=[NODE_A, NODE_B]),
            MagicMock(data=[]),
        ]
        db_mock, execute_mock = make_supabase_mock()
        execute_mock.side_effect = execute_results

        with patch("app.db.postgres_client._client", db_mock):
            response = TestClient(app).get(f"/papers/{PAPER_ID}/graph")

        nodes = response.json()["nodes"]
        assert nodes[0]["position"] == {"x": 0, "y": 0}
        assert nodes[1]["position"] == {"x": 250, "y": 0}


# ---------------------------------------------------------------------------
# GET /papers/{paper_id}/node/{node_id}
# ---------------------------------------------------------------------------

class TestGetNodeDetail:
    def test_node_not_found_returns_404(self, client):
        response = client.get(f"/papers/{PAPER_ID}/node/bad-id")
        assert response.status_code == 404

    def test_returns_node_with_neighbors(self):
        execute_results = [
            MagicMock(data=[NODE_A]),                           # node lookup
            MagicMock(data=[EDGE_AB]),                          # out_edges
            MagicMock(data=[]),                                 # in_edges
            MagicMock(data=[{"id": NODE_ID_B, "title": "Transformer", "type": "concept"}]),  # neighbor
        ]
        db_mock, execute_mock = make_supabase_mock()
        execute_mock.side_effect = execute_results

        with patch("app.db.postgres_client._client", db_mock):
            response = TestClient(app).get(f"/papers/{PAPER_ID}/node/{NODE_ID_A}")

        assert response.status_code == 200
        body = response.json()
        assert len(body["neighbors"]) == 1
        assert body["neighbors"][0]["id"] == NODE_ID_B
        assert body["neighbors"][0]["relationship"] == "BUILDS_ON"

    def test_node_with_no_edges_returns_empty_neighbors(self):
        execute_results = [
            MagicMock(data=[NODE_A]),
            MagicMock(data=[]),   # out_edges
            MagicMock(data=[]),   # in_edges
        ]
        db_mock, execute_mock = make_supabase_mock()
        execute_mock.side_effect = execute_results

        with patch("app.db.postgres_client._client", db_mock):
            response = TestClient(app).get(f"/papers/{PAPER_ID}/node/{NODE_ID_A}")

        assert response.status_code == 200
        assert response.json()["neighbors"] == []

    def test_response_includes_all_node_fields(self):
        execute_results = [
            MagicMock(data=[NODE_A]),
            MagicMock(data=[]),
            MagicMock(data=[]),
        ]
        db_mock, execute_mock = make_supabase_mock()
        execute_mock.side_effect = execute_results

        with patch("app.db.postgres_client._client", db_mock):
            response = TestClient(app).get(f"/papers/{PAPER_ID}/node/{NODE_ID_A}")

        body = response.json()
        expected_keys = {
            "id", "type", "title", "description", "simplified_explanation",
            "advantages", "limitations", "key_equations", "source_text",
            "section_name", "section_number", "page_number", "label",
            "neighbors",
        }
        assert expected_keys.issubset(body.keys())

    def test_incoming_edge_neighbor_included(self):
        # NODE_B -> NODE_A (incoming to A)
        edge_ba = {**EDGE_AB, "id": "edge-ba", "source_node_id": NODE_ID_B, "target_node_id": NODE_ID_A}
        execute_results = [
            MagicMock(data=[NODE_A]),
            MagicMock(data=[]),       # out_edges (none)
            MagicMock(data=[edge_ba]),  # in_edges
            MagicMock(data=[{"id": NODE_ID_B, "title": "Transformer", "type": "concept"}]),
        ]
        db_mock, execute_mock = make_supabase_mock()
        execute_mock.side_effect = execute_results

        with patch("app.db.postgres_client._client", db_mock):
            response = TestClient(app).get(f"/papers/{PAPER_ID}/node/{NODE_ID_A}")

        body = response.json()
        assert any(n["id"] == NODE_ID_B for n in body["neighbors"])


# ---------------------------------------------------------------------------
# POST /graph/expand
# ---------------------------------------------------------------------------

class TestExpandGraph:
    def test_node_not_found_returns_404(self, client):
        response = client.post("/graph/expand", json={"node_id": "bad-id", "hops": 1})
        assert response.status_code == 404

    def test_one_hop_returns_start_and_neighbors(self):
        execute_results = [
            MagicMock(data=[NODE_A]),      # start node
            MagicMock(data=[EDGE_AB]),     # out_edges from A
            MagicMock(data=[]),            # in_edges to A
            MagicMock(data=[NODE_B]),      # fetch neighbor B
        ]
        db_mock, execute_mock = make_supabase_mock()
        execute_mock.side_effect = execute_results

        with patch("app.db.postgres_client._client", db_mock):
            response = TestClient(app).post(
                "/graph/expand", json={"node_id": NODE_ID_A, "hops": 1}
            )

        assert response.status_code == 200
        body = response.json()
        returned_ids = {n["id"] for n in body["nodes"]}
        assert NODE_ID_A in returned_ids
        assert NODE_ID_B in returned_ids
        assert body["edges"][0]["id"] == EDGE_ID

    def test_zero_hops_returns_only_start_node(self):
        execute_results = [
            MagicMock(data=[NODE_A]),
        ]
        db_mock, execute_mock = make_supabase_mock()
        execute_mock.side_effect = execute_results

        with patch("app.db.postgres_client._client", db_mock):
            response = TestClient(app).post(
                "/graph/expand", json={"node_id": NODE_ID_A, "hops": 0}
            )

        assert response.status_code == 200
        body = response.json()
        assert len(body["nodes"]) == 1
        assert body["nodes"][0]["id"] == NODE_ID_A
        assert body["edges"] == []

    def test_response_nodes_are_react_flow_format(self):
        execute_results = [
            MagicMock(data=[NODE_A]),
            MagicMock(data=[]),
            MagicMock(data=[]),
        ]
        db_mock, execute_mock = make_supabase_mock()
        execute_mock.side_effect = execute_results

        with patch("app.db.postgres_client._client", db_mock):
            response = TestClient(app).post(
                "/graph/expand", json={"node_id": NODE_ID_A, "hops": 1}
            )

        node = response.json()["nodes"][0]
        assert "id" in node
        assert "type" in node
        assert "data" in node
        assert "position" in node

    def test_response_edges_are_react_flow_format(self):
        execute_results = [
            MagicMock(data=[NODE_A]),
            MagicMock(data=[EDGE_AB]),
            MagicMock(data=[]),
            MagicMock(data=[NODE_B]),
        ]
        db_mock, execute_mock = make_supabase_mock()
        execute_mock.side_effect = execute_results

        with patch("app.db.postgres_client._client", db_mock):
            response = TestClient(app).post(
                "/graph/expand", json={"node_id": NODE_ID_A, "hops": 1}
            )

        edge = response.json()["edges"][0]
        assert "id" in edge
        assert "source" in edge
        assert "target" in edge
        assert "label" in edge

    def test_cycles_do_not_produce_duplicates(self):
        edge_ba = {
            "id": "edge-ba",
            "paper_id": PAPER_ID,
            "source_node_id": NODE_ID_B,
            "target_node_id": NODE_ID_A,
            "relationship_type": "BUILDS_ON",
        }
        # Hop 1 from A: out=[A->B], in=[B->A]; fetch B; frontier becomes {B}
        # Hop 2 from B: out=[A->B], in=[B->A]; both A and B already visited
        execute_results = [
            MagicMock(data=[NODE_A]),        # start
            # hop 1, node A:
            MagicMock(data=[EDGE_AB]),       # out_edges from A
            MagicMock(data=[edge_ba]),       # in_edges to A
            MagicMock(data=[NODE_B]),        # fetch B
            # hop 2, node B:
            MagicMock(data=[EDGE_AB]),       # out_edges from B (A->B, but A already visited)
            MagicMock(data=[edge_ba]),       # in_edges to B (B->A, A already visited)
        ]
        db_mock, execute_mock = make_supabase_mock()
        execute_mock.side_effect = execute_results

        with patch("app.db.postgres_client._client", db_mock):
            response = TestClient(app).post(
                "/graph/expand", json={"node_id": NODE_ID_A, "hops": 2}
            )

        body = response.json()
        returned_ids = [n["id"] for n in body["nodes"]]
        assert returned_ids.count(NODE_ID_A) == 1
        assert returned_ids.count(NODE_ID_B) == 1
