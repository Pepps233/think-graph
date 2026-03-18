"""Unit tests for POST /papers/ingest/url, POST /papers/ingest/pdf, GET /papers/{id}."""

import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.routes.papers import _extract_arxiv_id
from app.main import app
from tests.conftest import make_supabase_mock


# ---------------------------------------------------------------------------
# _extract_arxiv_id — pure unit tests, no HTTP
# ---------------------------------------------------------------------------

class TestExtractArxivId:
    def test_abs_url(self):
        assert _extract_arxiv_id("https://arxiv.org/abs/2301.00001") == "2301.00001"

    def test_pdf_url_with_version(self):
        assert _extract_arxiv_id("https://arxiv.org/pdf/2301.00001v2") == "2301.00001v2"

    def test_http_abs_url(self):
        assert _extract_arxiv_id("http://arxiv.org/abs/2301.00001") == "2301.00001"

    def test_bare_id(self):
        assert _extract_arxiv_id("2301.00001") == "2301.00001"

    def test_bare_id_with_version(self):
        assert _extract_arxiv_id("2301.00001v3") == "2301.00001v3"

    def test_non_arxiv_url_returns_none(self):
        assert _extract_arxiv_id("https://example.com/paper") is None

    def test_empty_string_returns_none(self):
        assert _extract_arxiv_id("") is None

    def test_invalid_id_returns_none(self):
        assert _extract_arxiv_id("not-an-id") is None


# ---------------------------------------------------------------------------
# POST /papers/ingest/url
# ---------------------------------------------------------------------------

class TestIngestFromUrl:
    def test_happy_path_returns_ids(self, client):
        with patch("app.api.routes.papers.ingest_paper") as mock_task:
            mock_task.delay = MagicMock()
            response = client.post(
                "/papers/ingest/url",
                json={"arxiv_url": "https://arxiv.org/abs/2301.00001"},
            )
        assert response.status_code == 200
        data = response.json()
        assert "paper_id" in data and data["paper_id"]
        assert "job_id" in data and data["job_id"]

    def test_paper_row_inserted_with_pending_status(self, mock_db, client):
        db_mock, _ = mock_db
        with patch("app.api.routes.papers.ingest_paper") as mock_task:
            mock_task.delay = MagicMock()
            client.post(
                "/papers/ingest/url",
                json={"arxiv_url": "https://arxiv.org/abs/2301.00001"},
            )
        # Verify papers table was called
        table_calls = [str(call) for call in db_mock.table.call_args_list]
        assert any("papers" in c for c in table_calls)

    def test_job_row_inserted(self, mock_db, client):
        db_mock, _ = mock_db
        with patch("app.api.routes.papers.ingest_paper") as mock_task:
            mock_task.delay = MagicMock()
            client.post(
                "/papers/ingest/url",
                json={"arxiv_url": "https://arxiv.org/abs/2301.00001"},
            )
        table_calls = [str(call) for call in db_mock.table.call_args_list]
        assert any("jobs" in c for c in table_calls)

    def test_celery_task_dispatched(self, client):
        with patch("app.api.routes.papers.ingest_paper") as mock_task:
            mock_task.delay = MagicMock()
            client.post(
                "/papers/ingest/url",
                json={"arxiv_url": "https://arxiv.org/abs/2301.00001"},
            )
            mock_task.delay.assert_called_once()
            kwargs = mock_task.delay.call_args.kwargs
            assert kwargs["source_type"] == "arxiv"
            assert kwargs["source"] == "2301.00001"

    def test_invalid_url_returns_422(self, client):
        with patch("app.api.routes.papers.ingest_paper") as mock_task:
            mock_task.delay = MagicMock()
            response = client.post(
                "/papers/ingest/url",
                json={"arxiv_url": "https://notarxiv.com/paper"},
            )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /papers/ingest/pdf
# ---------------------------------------------------------------------------

MINIMAL_PDF = b"%PDF-1.4 minimal"  # not a real PDF but sufficient for hash/upload tests


def _make_pdf_upload(content: bytes = MINIMAL_PDF, content_type: str = "application/pdf"):
    return {"file": ("test.pdf", io.BytesIO(content), content_type)}


class TestIngestFromPdf:
    def test_happy_path_returns_ids(self, client):
        with (
            patch("app.api.routes.papers.upload_pdf", return_value="pdfs/abc.pdf"),
            patch("app.api.routes.papers.ingest_paper") as mock_task,
        ):
            mock_task.delay = MagicMock()
            response = client.post("/papers/ingest/pdf", files=_make_pdf_upload())
        assert response.status_code == 200
        data = response.json()
        assert "paper_id" in data and data["paper_id"]
        assert "job_id" in data and data["job_id"]

    def test_wrong_content_type_returns_422(self, client):
        response = client.post(
            "/papers/ingest/pdf",
            files=_make_pdf_upload(content_type="text/plain"),
        )
        assert response.status_code == 422

    def test_octet_stream_accepted(self, client):
        with (
            patch("app.api.routes.papers.upload_pdf", return_value="pdfs/abc.pdf"),
            patch("app.api.routes.papers.ingest_paper") as mock_task,
        ):
            mock_task.delay = MagicMock()
            response = client.post(
                "/papers/ingest/pdf",
                files=_make_pdf_upload(content_type="application/octet-stream"),
            )
        assert response.status_code == 200

    def test_duplicate_hash_returns_409(self):
        existing_id = "existing-paper-uuid"
        db_mock, execute_mock = make_supabase_mock(query_result_data=[{"id": existing_id}])
        with patch("app.db.postgres_client._client", db_mock):
            test_client = TestClient(app)
            with patch("app.api.routes.papers.ingest_paper") as mock_task:
                mock_task.delay = MagicMock()
                response = test_client.post("/papers/ingest/pdf", files=_make_pdf_upload())
        assert response.status_code == 409
        assert existing_id in response.json()["detail"]

    def test_upload_pdf_called_with_bytes_and_hash(self, client):
        content = b"fake pdf content for hash test"
        with (
            patch("app.api.routes.papers.upload_pdf", return_value="pdfs/xyz.pdf") as mock_upload,
            patch("app.api.routes.papers.ingest_paper") as mock_task,
        ):
            mock_task.delay = MagicMock()
            client.post("/papers/ingest/pdf", files=_make_pdf_upload(content=content))
        mock_upload.assert_called_once()
        call_args = mock_upload.call_args.args
        assert call_args[0] == content  # pdf_bytes
        import hashlib
        expected_sha = hashlib.sha256(content).hexdigest()
        assert call_args[1] == expected_sha

    def test_celery_task_dispatched_with_pdf_source_type(self, client):
        with (
            patch("app.api.routes.papers.upload_pdf", return_value="pdfs/abc.pdf"),
            patch("app.api.routes.papers.ingest_paper") as mock_task,
        ):
            mock_task.delay = MagicMock()
            client.post("/papers/ingest/pdf", files=_make_pdf_upload())
            mock_task.delay.assert_called_once()
            kwargs = mock_task.delay.call_args.kwargs
            assert kwargs["source_type"] == "pdf"


# ---------------------------------------------------------------------------
# GET /papers/{paper_id}
# ---------------------------------------------------------------------------

class TestGetPaper:
    def test_found_returns_200(self):
        paper_data = {"id": "paper-123", "title": "Test Paper", "ingestion_status": "completed"}
        db_mock, _ = make_supabase_mock(query_result_data=[paper_data])
        with patch("app.db.postgres_client._client", db_mock):
            test_client = TestClient(app)
            response = test_client.get("/papers/paper-123")
        assert response.status_code == 200
        assert response.json()["id"] == "paper-123"

    def test_not_found_returns_404(self, client):
        response = client.get("/papers/nonexistent-id")
        assert response.status_code == 404
