"""
Persist extraction results to Supabase nodes/edges tables
and cache raw LLM outputs in papers.llm_cache.
"""

import uuid

from app.models.extraction import (
    PaperEntities,
    PaperRelationships,
    PaperReasoningFlow,
    NodeType,
)


def write_nodes(db, paper_id: str, entities: PaperEntities) -> dict[str, str]:
    """
    Insert one node row per entity.
    Returns {entity_title: node_id} for edge resolution.
    """
    node_map: dict[str, str] = {}

    for entity in entities.entities:
        node_id = str(uuid.uuid4())
        db.table("nodes").insert({
            "id": node_id,
            "paper_id": paper_id,
            "type": entity.type.value,
            "title": entity.title,
            "description": entity.description,
            "simplified_explanation": entity.simplified_explanation,
            "advantages": entity.advantages,
            "limitations": entity.limitations,
            "key_equations": entity.key_equations,
            "source_text": entity.source_text,
            "section_name": entity.section_name,
            "section_number": entity.section_number,
            "page_number": entity.page_number,
            "label": entity.label,
        }).execute()
        node_map[entity.title] = node_id

    return node_map


def write_edges(
    db,
    paper_id: str,
    relationships: PaperRelationships,
    node_map: dict[str, str],
) -> None:
    """
    Insert one edge row per relationship.
    Skips edges where either endpoint is not in node_map.
    """
    for rel in relationships.relationships:
        source_id = node_map.get(rel.source_title)
        target_id = node_map.get(rel.target_title)
        if not source_id or not target_id:
            continue
        db.table("edges").insert({
            "id": str(uuid.uuid4()),
            "paper_id": paper_id,
            "source_node_id": source_id,
            "target_node_id": target_id,
            "relationship_type": rel.relationship_type.value,
        }).execute()


def write_reasoning_nodes(
    db,
    paper_id: str,
    flow: PaperReasoningFlow,
    node_map: dict[str, str],
) -> None:
    """
    Insert reasoning-type nodes for each step in the flow and chain them
    with LEADS_TO edges in sequence.
    """
    prev_id: str | None = None

    for step in flow.steps:
        node_id = str(uuid.uuid4())
        db.table("nodes").insert({
            "id": node_id,
            "paper_id": paper_id,
            "type": NodeType.reasoning.value,
            "title": step.title,
            "description": step.description,
            "section_name": step.section_name,
            "page_number": step.page_number,
            "simplified_explanation": None,
            "advantages": [],
            "limitations": [],
            "key_equations": [],
            "source_text": None,
            "section_number": None,
            "label": None,
        }).execute()
        node_map[step.title] = node_id

        if prev_id:
            db.table("edges").insert({
                "id": str(uuid.uuid4()),
                "paper_id": paper_id,
                "source_node_id": prev_id,
                "target_node_id": node_id,
                "relationship_type": "LEADS_TO",
            }).execute()

        prev_id = node_id


def cache_llm_output(db, paper_id: str, key: str, data: dict) -> None:
    """
    Merge a single key into papers.llm_cache JSONB column.
    Fetches the current value, merges, then updates.
    """
    result = db.table("papers").select("llm_cache").eq("id", paper_id).execute()
    current: dict = {}
    if result.data and result.data[0].get("llm_cache"):
        current = result.data[0]["llm_cache"]
    current[key] = data
    db.table("papers").update({"llm_cache": current}).eq("id", paper_id).execute()
