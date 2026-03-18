"""
Four-pass GPT-4o extraction pipeline using instructor for structured outputs.

Pass 1: PaperStructure  — section map with numbers and page ranges
Pass 2: PaperEntities   — all entities with full provenance metadata
Pass 3: PaperRelationships — directed relationships between entities
Pass 4: PaperReasoningFlow — ordered argument chain
"""

import instructor
from openai import OpenAI

from app.config import settings
from app.models.extraction import (
    PaperEntities,
    PaperRelationships,
    PaperReasoningFlow,
    PaperStructure,
)
from app.services.pdf_parser import ParsedPaper

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
        f"Full text (first 6000 chars):\n{parsed.raw_text[:6000]}"
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
    Sections are prepended with their name and page range so the model
    can ground each entity's provenance accurately.
    """
    section_blocks = []
    for section in parsed.sections:
        header = f"[Section: {section.name} | Pages: {section.page_start}-{section.page_end}]"
        # Limit each section to 3000 chars to stay within context limits
        section_blocks.append(f"{header}\n{section.text[:3000]}")

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
                    "(e.g. 'Equation 6a', 'Figure 3', 'Table 1'). "
                    "Extract all significant concepts, methods, architectures, datasets, "
                    "experiments, results, citations, limitations, and future work items. "
                    "Include the verbatim source_text excerpt for each entity."
                ),
            },
            {"role": "user", "content": user_content},
        ],
        max_tokens=4096,
    )


# ---------------------------------------------------------------------------
# Pass 3: Relationships
# ---------------------------------------------------------------------------

def extract_relationships(
    parsed: ParsedPaper, entities: PaperEntities
) -> PaperRelationships:
    """
    Identify directed relationships between extracted entities.
    Only emits relationships where both source and target are in the entity list.
    """
    entity_list = "\n".join(
        f"- {e.title} ({e.type.value})" for e in entities.entities
    )

    user_content = (
        f"Paper entities:\n{entity_list}\n\n"
        f"Paper text (first 8000 chars):\n{parsed.raw_text[:8000]}"
    )

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
        max_tokens=2048,
    )


# ---------------------------------------------------------------------------
# Pass 4: Reasoning Flow
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
