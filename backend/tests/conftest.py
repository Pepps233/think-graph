import io
from unittest.mock import MagicMock, patch

import fitz
import pytest
from fastapi.testclient import TestClient

from app.main import app
from workers.celery_app import celery_app


# ---------------------------------------------------------------------------
# Supabase mock helpers
# ---------------------------------------------------------------------------

def make_supabase_mock(query_result_data=None):
    """
    Build a mock Supabase client that replicates the chained builder pattern:
      db.table("x").select("*").eq("id", v).execute()
    Returns (db_mock, execute_mock) so tests can inspect calls and set side_effect.
    """
    execute_mock = MagicMock()
    execute_mock.return_value.data = query_result_data if query_result_data is not None else []

    query_builder = MagicMock()
    for method in ("select", "insert", "update", "eq"):
        getattr(query_builder, method).return_value = query_builder
    query_builder.execute = execute_mock

    db_mock = MagicMock()
    db_mock.table.return_value = query_builder

    return db_mock, execute_mock


@pytest.fixture
def mock_db():
    """Patch the Supabase singleton and yield (db_mock, execute_mock)."""
    db_mock, execute_mock = make_supabase_mock()
    with patch("app.db.postgres_client._client", db_mock):
        yield db_mock, execute_mock


@pytest.fixture
def client(mock_db):
    """FastAPI TestClient with Supabase patched."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# PDF byte fixtures (real fitz, no network)
# ---------------------------------------------------------------------------

def _make_pdf(pages_content: list[str]) -> bytes:
    """
    Create a minimal valid PDF using PyMuPDF.
    Each element of pages_content becomes one page of text.
    """
    doc = fitz.open()
    for content in pages_content:
        page = doc.new_page()
        page.insert_text((72, 72), content, fontsize=12)
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


@pytest.fixture(scope="session")
def minimal_pdf_bytes():
    """1-page PDF with 'Abstract' and '1. Introduction' section headers."""
    content = "Abstract\n\nThis is the abstract text.\n\n1. Introduction\n\nThis is the introduction."
    return _make_pdf([content])


@pytest.fixture(scope="session")
def multi_section_pdf_bytes():
    """2-page PDF with section headers spread across pages."""
    page1 = "Abstract\n\nPage one content.\n\n1. Introduction\n\nIntro text here."
    page2 = "2. Related Work\n\nRelated work content.\n\n3. Methodology\n\nMethod text."
    return _make_pdf([page1, page2])


@pytest.fixture(scope="session")
def no_section_pdf_bytes():
    """1-page PDF with plain body text and no recognizable section headers."""
    content = "This paper presents a novel approach to solving the problem at hand. " * 10
    return _make_pdf([content])


# ---------------------------------------------------------------------------
# Celery eager mode (run tasks synchronously in tests)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True, scope="session")
def celery_eager():
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
    )


def _make_pdf_with_headers(
    headers: list[str],
    body_text: str = "Lorem ipsum dolor sit amet. " * 20,
    header_fontsize: float = 14,
    body_fontsize: float = 10,
) -> bytes:
    """
    Create a PDF with distinct header and body font sizes.
    Each header gets its own line followed by body text on the same page.
    """
    doc = fitz.open()
    page = doc.new_page()
    y = 72
    for header in headers:
        page.insert_text((72, y), header, fontsize=header_fontsize)
        y += header_fontsize + 4
        page.insert_text((72, y), body_text, fontsize=body_fontsize)
        y += body_fontsize * 3 + 20
        # Start a new page if running low on space
        if y > 700:
            page = doc.new_page()
            y = 72
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()
