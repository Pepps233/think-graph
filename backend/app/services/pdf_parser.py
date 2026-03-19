from __future__ import annotations

import re
from dataclasses import dataclass

import fitz  # PyMuPDF


@dataclass
class Section:
    name: str
    page_start: int
    page_end: int
    text: str


@dataclass
class ParsedPaper:
    raw_text: str
    sections: list[Section]
    page_count: int
    page_texts: list[str]


def parse_pdf(pdf_bytes: bytes) -> ParsedPaper:
    """
    Extract raw text from PDF bytes.
    Page texts are preserved for later section re-segmentation
    once the LLM identifies the true section boundaries.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_texts: list[str] = []

    for page in doc:
        page_texts.append(page.get_text("text"))

    raw_text = "\n".join(page_texts)
    page_count = len(doc)
    doc.close()

    # Provide the full text as a single section initially.
    # The extraction pipeline will re-segment after the LLM
    # identifies the real section structure.
    sections = [
        Section(
            name="Full Text",
            page_start=1,
            page_end=page_count,
            text=raw_text,
        )
    ]

    return ParsedPaper(
        raw_text=raw_text,
        sections=sections,
        page_count=page_count,
        page_texts=page_texts,
    )


def rebuild_sections_from_structure(
    page_texts: list[str],
    section_infos: list[dict],
) -> list[Section]:
    """
    Re-segment the paper text using LLM-identified section boundaries.

    section_infos: list of dicts with keys:
        section_number, section_name, page_start, page_end (optional)
    """
    if not section_infos:
        return [
            Section(
                name="Full Text",
                page_start=1,
                page_end=len(page_texts),
                text="\n".join(page_texts),
            )
        ]

    total_pages = len(page_texts)
    sections: list[Section] = []

    for i, info in enumerate(section_infos):
        name = info.get("section_name", "")
        number = info.get("section_number", "")
        header = f"{number} {name}".strip() if number else name

        page_start = info.get("page_start", 1)
        page_end = info.get("page_end")

        # If page_end is missing, infer from the next section's start
        if page_end is None:
            if i + 1 < len(section_infos):
                next_start = section_infos[i + 1].get("page_start", total_pages)
                page_end = max(page_start, next_start)
            else:
                page_end = total_pages

        # Clamp to valid range
        page_start = max(1, min(page_start, total_pages))
        page_end = max(page_start, min(page_end, total_pages))

        section_text = "\n".join(page_texts[page_start - 1 : page_end])

        # Try to trim text to only the content between this header and the next
        section_text = _trim_to_section(
            section_text,
            header,
            section_infos[i + 1] if i + 1 < len(section_infos) else None,
        )

        sections.append(
            Section(
                name=header,
                page_start=page_start,
                page_end=page_end,
                text=section_text,
            )
        )

    return sections


def _trim_to_section(
    text: str,
    header: str,
    next_info: dict | None,
) -> str:
    """
    Best-effort trim: find the header line in the text and start from there.
    If a next section header is known, stop before it.
    """
    lines = text.splitlines()
    header_lower = header.lower().strip()

    # Find where this section's header appears
    start_idx = 0
    for i, line in enumerate(lines):
        if header_lower and _fuzzy_header_match(line, header_lower):
            start_idx = i
            break

    # Find where the next section starts (if known)
    end_idx = len(lines)
    if next_info:
        next_name = next_info.get("section_name", "")
        next_number = next_info.get("section_number", "")
        next_header = f"{next_number} {next_name}".strip() if next_number else next_name
        next_lower = next_header.lower().strip()

        if next_lower:
            for i in range(start_idx + 1, len(lines)):
                if _fuzzy_header_match(lines[i], next_lower):
                    end_idx = i
                    break

    return "\n".join(lines[start_idx:end_idx])


def _fuzzy_header_match(line: str, header_lower: str) -> bool:
    """Check if a line matches a section header (case-insensitive, flexible whitespace)."""
    stripped = line.strip().lower()
    if not stripped:
        return False
    # Normalize whitespace for comparison
    normalized_line = re.sub(r"\s+", " ", stripped)
    normalized_header = re.sub(r"\s+", " ", header_lower)
    return normalized_line == normalized_header or normalized_line.startswith(normalized_header)
