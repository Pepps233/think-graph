from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.postgres_client import get_client
from app.services.storage import presign_url

router = APIRouter(tags=["graph"])

def _node_to_rf(node: dict, index: int) -> dict:
    return {
        "id": node["id"],
        "type": node["type"],
        "data": {
            "title": node["title"],
            "description": node["description"],
            "type": node["type"],
            "simplified_explanation": node.get("simplified_explanation"),
            "advantages": node.get("advantages") or [],
            "limitations": node.get("limitations") or [],
            "key_equations": node.get("key_equations") or [],
            "source_text": node.get("source_text"),
            "section_name": node.get("section_name"),
            "section_number": node.get("section_number"),
            "page_number": node.get("page_number"),
            "label": node.get("label"),
            "image_url": presign_url(node["image_url"]) if node.get("image_url") else None,
        },
        "position": {"x": 0, "y": 0},
    }


def _edge_to_rf(edge: dict) -> dict:
    return {
        "id": edge["id"],
        "source": edge["source_node_id"],
        "target": edge["target_node_id"],
        "label": edge["relationship_type"],
    }


@router.get("/papers/{paper_id}/graph")
async def get_graph(paper_id: str):
    db = get_client()

    paper_check = db.table("papers").select("id").eq("id", paper_id).execute()
    if not paper_check.data:
        raise HTTPException(status_code=404, detail="Paper not found")

    nodes_result = db.table("nodes").select("*").eq("paper_id", paper_id).execute()
    edges_result = db.table("edges").select("*").eq("paper_id", paper_id).execute()

    rf_nodes = [_node_to_rf(n, i) for i, n in enumerate(nodes_result.data)]
    rf_edges = [_edge_to_rf(e) for e in edges_result.data]

    return {"nodes": rf_nodes, "edges": rf_edges}


@router.get("/papers/{paper_id}/node/{node_id}")
async def get_node_detail(paper_id: str, node_id: str):
    db = get_client()

    node_result = (
        db.table("nodes").select("*").eq("id", node_id).eq("paper_id", paper_id).execute()
    )
    if not node_result.data:
        raise HTTPException(status_code=404, detail="Node not found")

    node = node_result.data[0]

    out_edges = db.table("edges").select("*").eq("source_node_id", node_id).execute()
    in_edges = db.table("edges").select("*").eq("target_node_id", node_id).execute()

    neighbors = []

    for edge in out_edges.data:
        neighbor_result = (
            db.table("nodes")
            .select("id, title, type")
            .eq("id", edge["target_node_id"])
            .execute()
        )
        if neighbor_result.data:
            n = neighbor_result.data[0]
            neighbors.append(
                {
                    "id": n["id"],
                    "title": n["title"],
                    "type": n["type"],
                    "relationship": edge["relationship_type"],
                }
            )

    for edge in in_edges.data:
        neighbor_result = (
            db.table("nodes")
            .select("id, title, type")
            .eq("id", edge["source_node_id"])
            .execute()
        )
        if neighbor_result.data:
            n = neighbor_result.data[0]
            neighbors.append(
                {
                    "id": n["id"],
                    "title": n["title"],
                    "type": n["type"],
                    "relationship": edge["relationship_type"],
                }
            )

    return {**node, "neighbors": neighbors}


class ExpandRequest(BaseModel):
    node_id: str
    hops: int = 1


@router.post("/graph/expand")
async def expand_graph(body: ExpandRequest):
    db = get_client()

    start_result = db.table("nodes").select("*").eq("id", body.node_id).execute()
    if not start_result.data:
        raise HTTPException(status_code=404, detail="Node not found")

    visited_node_ids: set[str] = {body.node_id}
    visited_edge_ids: set[str] = set()
    frontier: set[str] = {body.node_id}
    collected_nodes: list[dict] = [start_result.data[0]]
    collected_edges: list[dict] = []

    for _ in range(body.hops):
        next_frontier: set[str] = set()

        for nid in frontier:
            out_edges = db.table("edges").select("*").eq("source_node_id", nid).execute()
            in_edges = db.table("edges").select("*").eq("target_node_id", nid).execute()

            for edge in out_edges.data + in_edges.data:
                if edge["id"] not in visited_edge_ids:
                    visited_edge_ids.add(edge["id"])
                    collected_edges.append(edge)

                neighbor_id = (
                    edge["target_node_id"]
                    if edge["source_node_id"] == nid
                    else edge["source_node_id"]
                )
                if neighbor_id not in visited_node_ids:
                    visited_node_ids.add(neighbor_id)
                    next_frontier.add(neighbor_id)
                    neighbor_result = (
                        db.table("nodes").select("*").eq("id", neighbor_id).execute()
                    )
                    if neighbor_result.data:
                        collected_nodes.append(neighbor_result.data[0])

        frontier = next_frontier

    rf_nodes = [_node_to_rf(n, i) for i, n in enumerate(collected_nodes)]
    rf_edges = [_edge_to_rf(e) for e in collected_edges]

    return {"nodes": rf_nodes, "edges": rf_edges}
