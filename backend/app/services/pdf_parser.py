import re
from dataclasses import dataclass

import fitz  # PyMuPDF


SECTION_PATTERNS = [
    r"^(?:abstract)$",
    r"^\d+\.?\s+introduction",
    r"^\d+\.?\s+related\s+work",
    r"^\d+\.?\s+background",
    r"^\d+\.?\s+method(?:ology)?",
    r"^\d+\.?\s+approach",
    r"^\d+\.?\s+model",
    r"^\d+\.?\s+experiment",
    r"^\d+\.?\s+evaluation",
    r"^\d+\.?\s+result",
    r"^\d+\.?\s+discussion",
    r"^\d+\.?\s+conclusion",
    r"^\d+\.?\s+limitation",
    r"^\d+\.?\s+future",
    r"^\d+\.?\s+reference",
]


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


def _is_section_header(line: str) -> bool:
    stripped = line.strip().lower()
    if not stripped or len(stripped) > 80:
        return False
    return any(re.match(p, stripped) for p in SECTION_PATTERNS)


def parse_pdf(pdf_bytes: bytes) -> ParsedPaper:
    """
    Extract raw text and detect sections from PDF bytes.
    Uses PyMuPDF bounding boxes for page-accurate provenance.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_texts: list[str] = []

    for page in doc:
        page_texts.append(page.get_text("text"))

    raw_text = "\n".join(page_texts)
    page_count = len(doc)
    doc.close()

    sections = _detect_sections(page_texts)
    return ParsedPaper(raw_text=raw_text, sections=sections, page_count=page_count)


def _detect_sections(page_texts: list[str]) -> list[Section]:
    """
    Walk page-by-page and detect section boundaries by header matching.
    """
    found: list[tuple[str, int]] = []  # (section_name, page_index)

    for page_idx, text in enumerate(page_texts):
        for line in text.splitlines():
            if _is_section_header(line):
                found.append((line.strip(), page_idx + 1))  # 1-indexed

    sections: list[Section] = []
    for i, (name, page_start) in enumerate(found):
        page_end = found[i + 1][1] - 1 if i + 1 < len(found) else len(page_texts)
        section_text = "\n".join(
            page_texts[page_start - 1 : page_end]
        )
        sections.append(
            Section(
                name=name,
                page_start=page_start,
                page_end=page_end,
                text=section_text,
            )
        )

    # Fallback: no sections detected — treat whole paper as one chunk
    if not sections:
        sections = [
            Section(
                name="Full Text",
                page_start=1,
                page_end=len(page_texts),
                text="\n".join(page_texts),
            )
        ]

    return sections
