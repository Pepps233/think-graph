"""
Persist extraction results to Supabase nodes/edges tables
and cache raw LLM outputs in papers.llm_cache.
"""

import re
import uuid

from app.models.extraction import (
    PaperEntities,
    PaperRelationships,
    PaperReasoningFlow,
    NodeType,
)


def _match_image_url(label: str, image_urls: dict[str, str]) -> str | None:
    """
    Match an entity label like 'Figure 1', 'Figure 1: The Transformer',
    or 'Table 2' against the image_urls keys.
    Tries exact match first, then extracts the figure/table number
    and matches against 'Figure N' keys.
    """
    # Exact match
    url = image_urls.get(label)
    if url:
        return url

    # Extract number from label (e.g. "Figure 1: The Transformer" -> "1")
    match = re.search(r"(?:figure|table|fig\.?)\s*(\d+)", label, re.IGNORECASE)
    if match:
        number = match.group(1)
        # Try normalized keys
        for prefix in ("Figure", "Table"):
            url = image_urls.get(f"{prefix} {number}")
            if url:
                return url

    return None


def write_nodes(
    db,
    paper_id: str,
    entities: PaperEntities,
    image_urls: dict[str, str] | None = None,
) -> dict[str, str]:
    """
    Insert one node row per entity.
    image_urls: optional mapping of label (e.g. 'Figure 1') -> public URL.
    Returns {entity_title: node_id} for edge resolution.
    """
    node_map: dict[str, str] = {}

    for entity in entities.entities:
        node_id = str(uuid.uuid4())
        row = {
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
        }
        if entity.latex:
            row["key_equations"] = [entity.latex]
        if image_urls and entity.type.value in ("figure", "table"):
            url = None
            if entity.label:
                url = _match_image_url(entity.label, image_urls)
            # Fall back to page-based matching if label match fails
            if not url and entity.page_number:
                for key, candidate_url in image_urls.items():
                    if key.startswith(f"p{entity.page_number}_"):
                        url = candidate_url
                        break
            if url:
                row["image_url"] = url
        db.table("nodes").insert(row).execute()
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


def write_reasoning_edges(
    db,
    paper_id: str,
    flow: PaperReasoningFlow,
    node_map: dict[str, str],
) -> None:
    """
    Chain existing entity nodes with LEADS_TO edges following
    the paper's reasoning flow. No new nodes are created.
    """
    prev_id: str | None = None

    for step in flow.steps:
        node_id = node_map.get(step.entity_title)
        if not node_id:
            continue

        if prev_id and prev_id != node_id:
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
