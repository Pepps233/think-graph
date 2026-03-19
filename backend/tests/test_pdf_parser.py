"""Unit tests for app.services.pdf_parser — no network, real fitz."""

import pytest

from app.services.pdf_parser import (
    ParsedPaper,
    Section,
    parse_pdf,
    rebuild_sections_from_structure,
)


# ---------------------------------------------------------------------------
# parse_pdf
# ---------------------------------------------------------------------------

class TestParsePdf:
    def test_returns_parsed_paper_instance(self, minimal_pdf_bytes):
        result = parse_pdf(minimal_pdf_bytes)
        assert isinstance(result, ParsedPaper)

    def test_page_count_single_page(self, minimal_pdf_bytes):
        result = parse_pdf(minimal_pdf_bytes)
        assert result.page_count == 1

    def test_raw_text_is_non_empty(self, minimal_pdf_bytes):
        result = parse_pdf(minimal_pdf_bytes)
        assert len(result.raw_text.strip()) > 0

    def test_page_texts_preserved(self, multi_section_pdf_bytes):
        result = parse_pdf(multi_section_pdf_bytes)
        assert len(result.page_texts) == 2
        assert result.page_count == 2

    def test_initial_sections_is_full_text(self, minimal_pdf_bytes):
        result = parse_pdf(minimal_pdf_bytes)
        assert len(result.sections) == 1
        assert result.sections[0].name == "Full Text"

    def test_invalid_bytes_raises(self):
        with pytest.raises(Exception):
            parse_pdf(b"not a pdf")


# ---------------------------------------------------------------------------
# rebuild_sections_from_structure
# ---------------------------------------------------------------------------

class TestRebuildSectionsFromStructure:
    def test_empty_section_infos_returns_full_text(self):
        page_texts = ["Page one content.", "Page two content."]
        sections = rebuild_sections_from_structure(page_texts, [])
        assert len(sections) == 1
        assert sections[0].name == "Full Text"

    def test_single_section(self):
        page_texts = ["Abstract\n\nThis is the abstract."]
        infos = [{"section_number": "", "section_name": "Abstract", "page_start": 1}]
        sections = rebuild_sections_from_structure(page_texts, infos)
        assert len(sections) == 1
        assert sections[0].name == "Abstract"
        assert sections[0].page_start == 1
        assert sections[0].page_end == 1

    def test_multiple_sections_inferred_page_end(self):
        page_texts = [
            "Abstract\n\nAbstract content.",
            "1 Introduction\n\nIntro content.",
            "2 Methods\n\nMethod content.",
        ]
        infos = [
            {"section_number": "", "section_name": "Abstract", "page_start": 1},
            {"section_number": "1", "section_name": "Introduction", "page_start": 2},
            {"section_number": "2", "section_name": "Methods", "page_start": 3},
        ]
        sections = rebuild_sections_from_structure(page_texts, infos)
        assert len(sections) == 3
        assert sections[0].name == "Abstract"
        assert sections[1].name == "1 Introduction"
        assert sections[2].name == "2 Methods"
        # Last section should extend to the final page
        assert sections[2].page_end == 3

    def test_page_end_explicitly_set(self):
        page_texts = ["Abstract\n\nContent.", "More content."]
        infos = [
            {
                "section_number": "",
                "section_name": "Abstract",
                "page_start": 1,
                "page_end": 2,
            }
        ]
        sections = rebuild_sections_from_structure(page_texts, infos)
        assert sections[0].page_end == 2

    def test_page_start_clamped_to_valid_range(self):
        page_texts = ["Content."]
        infos = [{"section_number": "1", "section_name": "Intro", "page_start": 99}]
        sections = rebuild_sections_from_structure(page_texts, infos)
        assert sections[0].page_start == 1  # clamped to max valid

    def test_section_text_contains_content(self):
        page_texts = [
            "Abstract\n\nAbstract content here.",
            "1 Introduction\n\nIntro text follows.",
        ]
        infos = [
            {"section_number": "", "section_name": "Abstract", "page_start": 1},
            {"section_number": "1", "section_name": "Introduction", "page_start": 2},
        ]
        sections = rebuild_sections_from_structure(page_texts, infos)
        assert "Abstract content" in sections[0].text
        assert "Intro text" in sections[1].text

    def test_subsections_preserved(self):
        page_texts = [
            "3 Model Architecture\n\nOverview.\n\n3.1 Encoder\n\nEncoder details.\n\n3.2 Decoder\n\nDecoder details.",
        ]
        infos = [
            {"section_number": "3", "section_name": "Model Architecture", "page_start": 1},
            {"section_number": "3.1", "section_name": "Encoder", "page_start": 1},
            {"section_number": "3.2", "section_name": "Decoder", "page_start": 1},
        ]
        sections = rebuild_sections_from_structure(page_texts, infos)
        assert len(sections) == 3
        assert sections[0].name == "3 Model Architecture"
        assert sections[1].name == "3.1 Encoder"
        assert sections[2].name == "3.2 Decoder"
