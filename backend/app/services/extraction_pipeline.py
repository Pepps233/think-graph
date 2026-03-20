"""
GPT-4o extraction pipeline using instructor for structured outputs.

Pass 1: PaperStructure  — section map (PDF-native first, LLM fallback)
Pass 2: PaperEntities   — all entities with full provenance metadata
Pass 3: PaperRelationshipsAndReasoning — relationships + reasoning flow (merged)
"""

import instructor
from openai import OpenAI

from app.config import settings
from app.models.extraction import (
    PaperEntities,
    PaperRelationships,
    PaperReasoningFlow,
    PaperRelationshipsAndReasoning,
    PaperStructure,
)
from app.services.pdf_parser import ParsedPaper, rebuild_sections_from_structure

_client: instructor.Instructor | None = None


def _get_client() -> instructor.Instructor:
    global _client
    if _client is None:
        _client = instructor.from_openai(OpenAI(api_key=settings.openai_api_key))
    return _client


# ---------------------------------------------------------------------------
# Pass 1: Paper Structure
# ---------------------------------------------------------------------------

def extract_structure(parsed: ParsedPaper, metadata: dict) -> PaperStructure:
    """
    Extract/confirm the paper's section structure.
    Uses arXiv metadata as ground truth for title/abstract/authors.
    """
    title = metadata.get("title", "")
    abstract = metadata.get("abstract", "")
    authors = metadata.get("authors", [])
    authors_str = ", ".join(authors) if isinstance(authors, list) else str(authors)

    user_content = (
        f"Title: {title}\n"
        f"Authors: {authors_str}\n"
        f"Abstract: {abstract}\n\n"
        f"Full text:\n{parsed.raw_text[:30000]}"
    )

    return _get_client().chat.completions.create(
        model="gpt-4o",
        response_model=PaperStructure,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert at analyzing academic research papers. "
                    "Extract the paper's structure accurately, including all section "
                    "numbers, section names, and the page ranges they span."
                ),
            },
            {"role": "user", "content": user_content},
        ],
        max_tokens=2048,
    )


# ---------------------------------------------------------------------------
# Pass 2: Entities
# ---------------------------------------------------------------------------

def extract_entities(parsed: ParsedPaper, structure: PaperStructure) -> PaperEntities:
    """
    Extract all knowledge graph entities with full provenance metadata.
    Uses LLM-identified sections from PaperStructure to avoid missing
    content due to unrecognized section headers.
    """
    # Rebuild sections using the LLM-identified structure
    llm_sections = rebuild_sections_from_structure(
        parsed.page_texts,
        [s.model_dump() for s in structure.sections],
    )

    section_blocks = []
    for section in llm_sections:
        header = f"[Section: {section.name} | Pages: {section.page_start}-{section.page_end}]"
        section_blocks.append(f"{header}\n{section.text[:6500]}")

    sections_text = "\n\n".join(section_blocks)

    user_content = (
        f"Paper: {structure.title}\n\n"
        f"{sections_text}"
    )

    return _get_client().chat.completions.create(
        model="gpt-4o",
        response_model=PaperEntities,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert at extracting knowledge graph entities from academic papers. "
                    "For each entity, capture its exact provenance: the section name, section number, "
                    "page number (from the section header), and label if applicable "
                    "(e.g. 'Equation 1', 'Figure 3', 'Table 1'). "
                    "Extract all significant concepts, methods, architectures, datasets, "
                    "experiments, results, citations, limitations, and future work items. "
                    "Include the verbatim source_text excerpt for each entity.\n\n"
                    "EQUATIONS: Each significant equation MUST be its own entity with type='equation'. "
                    "Set the 'latex' field to the LaTeX representation of the equation. "
                    "The 'description' should explain the equation in depth: what each variable means, "
                    "how the equation works, why it matters, and how it connects to the paper's method. "
                    "The 'simplified_explanation' should explain the equation in plain language. "
                    "Use the 'label' field for the equation label (e.g. 'Equation 1'). "
                    "Do NOT put equations in the key_equations array of other entities.\n\n"
                    "FIGURES AND TABLES: Each figure, table, and graph MUST be its own entity. "
                    "Use type='figure' for figures/diagrams/graphs and type='table' for tables. "
                    "The 'description' should thoroughly describe what the figure/table shows, "
                    "its key takeaways, and how it relates to the paper's argument. "
                    "Use the 'label' field for the reference label (e.g. 'Figure 1', 'Table 2').\n\n"
                    "FIELD RELEVANCE BY TYPE -- omit fields that do not apply:\n"
                    "- equation: OMIT advantages, limitations. USE latex, description, simplified_explanation.\n"
                    "- figure, table: OMIT advantages, limitations, key_equations, latex. USE description, label.\n"
                    "- dataset: OMIT latex, key_equations. USE description, advantages, limitations.\n"
                    "- citation: OMIT advantages, limitations, key_equations, latex. USE description only.\n"
                    "- problem, limitation, future_work: OMIT latex, key_equations. USE description.\n"
                    "- method, architecture: USE all fields (advantages, limitations, key_equations, description, simplified_explanation).\n"
                    "- concept, experiment, result: OMIT latex. USE description, advantages, limitations as relevant.\n"
                    "Set omitted fields to null or empty list. Do NOT fabricate content for irrelevant fields."
                ),
            },
            {"role": "user", "content": user_content},
        ],
        max_tokens=8192,
    )


# ---------------------------------------------------------------------------
# Pass 3: Relationships
# ---------------------------------------------------------------------------

def extract_relationships(
    entities: PaperEntities,
) -> PaperRelationships:
    """
    Identify directed relationships between extracted entities.
    Only emits relationships where both source and target are in the entity list.
    """
    entity_list = "\n".join(
        f"- {e.title} ({e.type.value})"
        for e in entities.entities
    )

    user_content = f"Paper entities:\n{entity_list}"

    return _get_client().chat.completions.create(
        model="gpt-4o",
        response_model=PaperRelationships,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert at identifying directed relationships between entities "
                    "in academic papers. Only emit relationships where both the source and target "
                    "entity titles exactly match entries in the provided entity list. "
                    "Use the most specific relationship type available."
                ),
            },
            {"role": "user", "content": user_content},
        ],
        max_tokens=4096,
    )


# ---------------------------------------------------------------------------
# Pass 4: Reasoning Flow (standalone, kept for backward compatibility)
# ---------------------------------------------------------------------------

def extract_reasoning_flow(
    parsed: ParsedPaper, structure: PaperStructure
) -> PaperReasoningFlow:
    """
    Map the paper's logical argument chain from problem to conclusion.
    """
    section_overview = "\n".join(
        f"{s.section_number} {s.section_name}" for s in structure.sections
    )

    user_content = (
        f"Title: {structure.title}\n"
        f"Abstract: {structure.abstract}\n\n"
        f"Section overview:\n{section_overview}"
    )

    return _get_client().chat.completions.create(
        model="gpt-4o",
        response_model=PaperReasoningFlow,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert at mapping the logical argument structure of academic papers. "
                    "Extract the ordered reasoning chain from problem identification through to "
                    "conclusions: Problem → Limitations of Prior Work → Proposed Method → "
                    "Experiments → Results → Conclusion. "
                    "Each step should reference the section it comes from."
                ),
            },
            {"role": "user", "content": user_content},
        ],
        max_tokens=2048,
    )


# ---------------------------------------------------------------------------
# Pass 3+4 Merged: Relationships + Reasoning Flow
# ---------------------------------------------------------------------------

def extract_relationships_and_reasoning(
    entities: PaperEntities, structure: PaperStructure
) -> PaperRelationshipsAndReasoning:
    """
    Extract both relationships and reasoning flow in a single LLM call.
    """
    entity_list = "\n".join(
        f"- {e.title} ({e.type.value})"
        for e in entities.entities
    )

    section_overview = "\n".join(
        f"{s.section_number} {s.section_name}" for s in structure.sections
    )

    user_content = (
        f"Title: {structure.title}\n"
        f"Abstract: {structure.abstract}\n\n"
        f"Section overview:\n{section_overview}\n\n"
        f"Paper entities:\n{entity_list}"
    )

    return _get_client().chat.completions.create(
        model="gpt-4o",
        response_model=PaperRelationshipsAndReasoning,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert at analyzing academic research papers. "
                    "Perform BOTH tasks below.\n\n"
                    "TASK 1 - RELATIONSHIPS: Identify directed relationships between the provided entities. "
                    "Only emit relationships where both the source and target entity titles exactly match "
                    "entries in the entity list. Use the most specific relationship type available.\n\n"
                    "TASK 2 - REASONING FLOW: Extract the ordered reasoning chain from problem identification "
                    "through to conclusions: Problem -> Limitations of Prior Work -> Proposed Method -> "
                    "Experiments -> Results -> Conclusion. Each step should reference the section it comes from."
                ),
            },
            {"role": "user", "content": user_content},
        ],
        max_tokens=4096,
    )
