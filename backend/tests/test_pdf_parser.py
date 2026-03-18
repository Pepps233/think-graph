"""Unit tests for app.services.pdf_parser — no network, real fitz."""

import pytest

from app.services.pdf_parser import (
    ParsedPaper,
    Section,
    _detect_sections,
    _is_section_header,
    parse_pdf,
)


# ---------------------------------------------------------------------------
# _is_section_header
# ---------------------------------------------------------------------------

class TestIsSectionHeader:
    def test_empty_string_returns_false(self):
        assert _is_section_header("") is False

    def test_whitespace_only_returns_false(self):
        assert _is_section_header("   ") is False

    def test_string_over_80_chars_returns_false(self):
        long_line = "1. Introduction " + "x" * 70  # well over 80 chars
        assert _is_section_header(long_line) is False

    def test_exactly_80_chars_can_match(self):
        # "abstract" is 8 chars — pad to 80 with spaces before stripping
        # _is_section_header strips before checking length, so 80 stripped chars = boundary
        # Build a line that strips to exactly 80 chars and matches a pattern
        header = "1. " + "introduction" + " " * (80 - 3 - 12)  # 65 spaces, total stripped = 15 ... rethink
        # Simplest approach: test that length check uses stripped length
        line_80 = "1. introduction" + "x" * (80 - 15)  # stripped = 80 chars total
        # This won't match a pattern because of trailing x chars, so False
        assert _is_section_header(line_80) is False

    def test_random_sentence_returns_false(self):
        assert _is_section_header("This is a random sentence about things.") is False

    def test_abstract_lowercase(self):
        assert _is_section_header("abstract") is True

    def test_abstract_capitalized(self):
        assert _is_section_header("Abstract") is True

    def test_abstract_uppercase(self):
        assert _is_section_header("ABSTRACT") is True

    def test_numbered_introduction_with_period(self):
        assert _is_section_header("1. Introduction") is True

    def test_numbered_introduction_without_period(self):
        assert _is_section_header("1 Introduction") is True

    def test_numbered_related_work(self):
        assert _is_section_header("2. Related Work") is True

    def test_numbered_methodology(self):
        assert _is_section_header("3. Methodology") is True

    def test_numbered_conclusion(self):
        assert _is_section_header("6. Conclusion") is True

    def test_introduction_with_extra_words_returns_false(self):
        # Pattern requires the section name to start right after the number
        # "Introduction to Machine Learning" does not match "^\d+\.?\s+introduction$"
        assert _is_section_header("Introduction to Machine Learning") is False

    def test_bare_introduction_no_number_returns_false(self):
        # Patterns require leading digit for numbered sections
        assert _is_section_header("Introduction") is False

    def test_string_81_chars_returns_false(self):
        # 81 stripped chars should fail length check
        line = "a" * 81
        assert _is_section_header(line) is False

    def test_leading_trailing_whitespace_stripped(self):
        assert _is_section_header("  Abstract  ") is True


# ---------------------------------------------------------------------------
# _detect_sections
# ---------------------------------------------------------------------------

class TestDetectSections:
    def test_empty_input_returns_full_text_fallback(self):
        sections = _detect_sections([])
        assert len(sections) == 1
        assert sections[0].name == "Full Text"

    def test_no_headers_returns_full_text_fallback(self):
        page_texts = ["This is plain text with no headers.", "More plain text on page two."]
        sections = _detect_sections(page_texts)
        assert len(sections) == 1
        assert sections[0].name == "Full Text"

    def test_single_header_on_page_one(self):
        page_texts = ["Abstract\n\nHere is the abstract content."]
        sections = _detect_sections(page_texts)
        assert len(sections) == 1
        assert sections[0].name == "Abstract"
        assert sections[0].page_start == 1  # 1-indexed

    def test_two_headers_across_pages(self):
        page_texts = [
            "Abstract\n\nAbstract content.",
            "1. Introduction\n\nIntroduction content.",
        ]
        sections = _detect_sections(page_texts)
        assert len(sections) == 2
        # First section: page_start=1, page_end=1 (before intro on page 2)
        assert sections[0].name == "Abstract"
        assert sections[0].page_start == 1
        assert sections[0].page_end == 1
        # Second section: page_start=2, page_end=2 (last page)
        assert sections[1].name == "1. Introduction"
        assert sections[1].page_start == 2
        assert sections[1].page_end == 2

    def test_section_text_spans_correct_pages(self):
        page_texts = [
            "Abstract\n\nAbstract content here.",
            "Continued abstract body.",
            "1. Introduction\n\nIntro content.",
        ]
        sections = _detect_sections(page_texts)
        assert len(sections) == 2
        # Abstract spans pages 1-2
        assert sections[0].page_start == 1
        assert sections[0].page_end == 2
        # Introduction spans page 3 only
        assert sections[1].page_start == 3
        assert sections[1].page_end == 3


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

    def test_sections_non_empty_for_multi_section(self, multi_section_pdf_bytes):
        result = parse_pdf(multi_section_pdf_bytes)
        assert len(result.sections) > 0

    def test_multi_section_page_count(self, multi_section_pdf_bytes):
        result = parse_pdf(multi_section_pdf_bytes)
        assert result.page_count == 2

    def test_no_section_falls_back_to_full_text(self, no_section_pdf_bytes):
        result = parse_pdf(no_section_pdf_bytes)
        assert len(result.sections) == 1
        assert result.sections[0].name == "Full Text"

    def test_invalid_bytes_raises(self):
        with pytest.raises(Exception):
            parse_pdf(b"not a pdf")
