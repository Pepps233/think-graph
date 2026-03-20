from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

import fitz  # PyMuPDF

from app.models.extraction import PaperStructure, SectionInfo


@dataclass
class ExtractedImage:
    """An image extracted from a PDF page."""
    image_bytes: bytes
    page_number: int  # 1-indexed
    image_index: int  # index within the page
    width: int
    height: int
    ext: str  # file extension: png, jpeg, etc.


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
    images: list[ExtractedImage] = field(default_factory=list)


def parse_pdf(pdf_bytes: bytes) -> ParsedPaper:
    """
    Extract raw text and images from PDF bytes.
    Page texts are preserved for later section re-segmentation
    once the LLM identifies the true section boundaries.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_texts: list[str] = []
    images: list[ExtractedImage] = []

    for page_idx, page in enumerate(doc):
        page_texts.append(page.get_text("text"))

        # Extract images from this page
        for img_idx, img_info in enumerate(page.get_images(full=True)):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            if not base_image:
                continue

            width = base_image.get("width", 0)
            height = base_image.get("height", 0)

            # Skip tiny images (icons, decorations, line art)
            if width < 100 or height < 100:
                continue

            images.append(
                ExtractedImage(
                    image_bytes=base_image["image"],
                    page_number=page_idx + 1,
                    image_index=img_idx,
                    width=width,
                    height=height,
                    ext=base_image.get("ext", "png"),
                )
            )

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
        images=images,
    )


def extract_structure_from_fonts(
    pdf_bytes: bytes, metadata: dict
) -> PaperStructure | None:
    """
    Try to extract paper structure without an LLM call.

    Strategy:
    1. Use PDF bookmarks (get_toc) if available.
    2. Otherwise, detect section headers via font-size heuristics.

    Returns PaperStructure if successful, None to signal LLM fallback.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(doc)

    title = metadata.get("title", "")
    abstract = metadata.get("abstract", "")
    authors = metadata.get("authors", [])
    if isinstance(authors, str):
        authors = [a.strip() for a in authors.split(",")]

    # --- Strategy 1: PDF bookmarks / TOC ---
    toc = doc.get_toc()  # [[level, title, page], ...]
    if toc:
        sections = _sections_from_toc(toc, total_pages)
        if len(sections) >= 3:
            doc.close()
            return PaperStructure(
                title=title,
                abstract=abstract,
                authors=authors,
                sections=sections,
            )

    # --- Strategy 2: Font-size heuristics ---
    sections = _sections_from_font_sizes(doc)
    doc.close()

    if len(sections) >= 3:
        return PaperStructure(
            title=title,
            abstract=abstract,
            authors=authors,
            sections=sections,
        )

    return None  # Not enough structure found — fall back to LLM


# -- Section number pattern: "1", "1.", "1.2", "A", "A.1", "IV", etc. --
_SECTION_NUM_RE = re.compile(
    r"^([A-Z](?:\.\d+)?|\d+(?:\.\d+)*\.?|[IVXLC]+\.?)\s+"
)


def _sections_from_toc(
    toc: list[list], total_pages: int
) -> list[SectionInfo]:
    """Convert PyMuPDF TOC entries into SectionInfo list."""
    sections: list[SectionInfo] = []
    for i, entry in enumerate(toc):
        level, raw_title, page = entry[0], entry[1], entry[2]
        if level > 2:
            continue  # skip sub-subsections

        raw_title = raw_title.strip()
        if not raw_title:
            continue

        m = _SECTION_NUM_RE.match(raw_title)
        if m:
            section_number = m.group(1).rstrip(".")
            section_name = raw_title[m.end():].strip()
        else:
            section_number = ""
            section_name = raw_title

        # page_end: next section's page or last page
        page_end = total_pages
        for j in range(i + 1, len(toc)):
            if toc[j][0] <= level:
                page_end = toc[j][2]
                break

        sections.append(
            SectionInfo(
                section_number=section_number,
                section_name=section_name,
                page_start=max(1, page),
                page_end=min(page_end, total_pages),
            )
        )

    return sections


def _sections_from_font_sizes(doc: fitz.Document) -> list[SectionInfo]:
    """
    Detect section headers by finding text spans whose font size is larger
    than the body text.  Works for most single/double-column papers.
    """
    # First pass: collect font sizes across all pages to find body size
    size_counts: Counter[float] = Counter()
    for page in doc:
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        for block in blocks:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span["text"].strip()
                    if len(text) > 3:  # skip tiny fragments
                        size_counts[round(span["size"], 1)] += len(text)

    if not size_counts:
        return []

    body_size = size_counts.most_common(1)[0][0]

    # Second pass: find lines with font size > body that look like headers
    candidates: list[tuple[str, int]] = []  # (header_text, page_number)
    for page_idx, page in enumerate(doc):
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        for block in blocks:
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue

                line_text = "".join(s["text"] for s in spans).strip()
                if not line_text or len(line_text) > 120:
                    continue  # skip empty or too-long lines

                max_span_size = max(s["size"] for s in spans)
                if max_span_size <= body_size:
                    continue

                # Check if it looks like a section header
                is_bold = any(
                    "bold" in s.get("font", "").lower() for s in spans
                )
                has_number = _SECTION_NUM_RE.match(line_text) is not None

                if has_number or (is_bold and max_span_size >= body_size + 1.5):
                    candidates.append((line_text, page_idx + 1))

    # Filter out the title (usually largest font on page 1) and junk
    if not candidates:
        return []

    sections: list[SectionInfo] = []
    for i, (raw_header, page_num) in enumerate(candidates):
        m = _SECTION_NUM_RE.match(raw_header)
        if m:
            section_number = m.group(1).rstrip(".")
            section_name = raw_header[m.end():].strip()
        else:
            section_number = ""
            section_name = raw_header

        # Skip likely title/author lines on first page
        if page_num == 1 and not section_number and i < 2:
            continue

        page_end = (
            candidates[i + 1][1] if i + 1 < len(candidates) else len(doc)
        )

        sections.append(
            SectionInfo(
                section_number=section_number,
                section_name=section_name,
                page_start=page_num,
                page_end=page_end,
            )
        )

    return sections


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
