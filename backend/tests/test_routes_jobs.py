"""Unit tests for GET /jobs/{id} and GET /jobs/{id}/stream (SSE)."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import make_supabase_mock


JOB_DATA = {
    "id": "job-123",
    "paper_id": "paper-456",
    "status": "completed",
    "current_step": "Done",
    "progress": 100,
    "error_message": None,
}


# ---------------------------------------------------------------------------
# GET /jobs/{job_id}
# ---------------------------------------------------------------------------

class TestGetJob:
    def test_found_returns_200(self):
        db_mock, _ = make_supabase_mock(query_result_data=[JOB_DATA])
        with patch("app.db.postgres_client._client", db_mock):
            test_client = TestClient(app)
            response = test_client.get("/jobs/job-123")
        assert response.status_code == 200
        assert response.json()["id"] == "job-123"

    def test_not_found_returns_404(self, client):
        # mock_db fixture yields empty data by default
        response = client.get("/jobs/nonexistent")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /jobs/{job_id}/stream  — SSE
# ---------------------------------------------------------------------------

def _parse_sse_events(body: str) -> list[dict]:
    """Extract and parse JSON payloads from SSE text body."""
    events = []
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            payload = line[len("data:"):].strip()
            events.append(json.loads(payload))
    return events


class TestStreamJob:
    def test_nonexistent_job_returns_404(self, client):
        # Default mock_db returns empty data -> job not found
        response = client.get("/jobs/nonexistent/stream")
        assert response.status_code == 404

    def test_completed_job_returns_event_stream_content_type(self):
        # First call: exists check. Second call: poll.
        check_data = [{"id": "job-123"}]
        poll_data = [JOB_DATA]

        execute_results = [
            MagicMock(data=check_data),
            MagicMock(data=poll_data),
        ]

        db_mock, execute_mock = make_supabase_mock()
        execute_mock.side_effect = execute_results

        with patch("app.db.postgres_client._client", db_mock):
            with patch("app.api.routes.jobs.POLL_INTERVAL", 0):
                test_client = TestClient(app)
                response = test_client.get("/jobs/job-123/stream")

        assert "text/event-stream" in response.headers["content-type"]

    def test_completed_job_stream_contains_data_event(self):
        check_data = [{"id": "job-123"}]
        poll_data = [JOB_DATA]
        execute_results = [
            MagicMock(data=check_data),
            MagicMock(data=poll_data),
        ]
        db_mock, execute_mock = make_supabase_mock()
        execute_mock.side_effect = execute_results

        with patch("app.db.postgres_client._client", db_mock):
            with patch("app.api.routes.jobs.POLL_INTERVAL", 0):
                test_client = TestClient(app)
                response = test_client.get("/jobs/job-123/stream")

        events = _parse_sse_events(response.text)
        assert len(events) >= 1
        assert events[0]["id"] == "job-123"
        assert events[0]["status"] == "completed"

    def test_failed_job_stream_ends_after_one_event(self):
        failed_job = {**JOB_DATA, "status": "failed", "error_message": "Something went wrong"}
        check_data = [{"id": "job-123"}]
        execute_results = [
            MagicMock(data=check_data),
            MagicMock(data=[failed_job]),
        ]
        db_mock, execute_mock = make_supabase_mock()
        execute_mock.side_effect = execute_results

        with patch("app.db.postgres_client._client", db_mock):
            with patch("app.api.routes.jobs.POLL_INTERVAL", 0):
                test_client = TestClient(app)
                response = test_client.get("/jobs/job-123/stream")

        events = _parse_sse_events(response.text)
        assert len(events) == 1
        assert events[0]["status"] == "failed"

    def test_sse_event_json_contains_all_fields(self):
        check_data = [{"id": "job-123"}]
        execute_results = [
            MagicMock(data=check_data),
            MagicMock(data=[JOB_DATA]),
        ]
        db_mock, execute_mock = make_supabase_mock()
        execute_mock.side_effect = execute_results

        with patch("app.db.postgres_client._client", db_mock):
            with patch("app.api.routes.jobs.POLL_INTERVAL", 0):
                test_client = TestClient(app)
                response = test_client.get("/jobs/job-123/stream")

        events = _parse_sse_events(response.text)
        required_fields = {"id", "paper_id", "status", "current_step", "progress", "error_message"}
        assert required_fields.issubset(events[0].keys())

    def test_multi_poll_emits_two_events_then_ends(self):
        """Mock DB returns 'processing' on first poll, 'completed' on second."""
        processing_job = {**JOB_DATA, "status": "processing", "progress": 50, "current_step": "Extracting entities"}
        completed_job = {**JOB_DATA, "status": "completed", "progress": 100}

        check_data = [{"id": "job-123"}]
        execute_results = [
            MagicMock(data=check_data),    # existence check
            MagicMock(data=[processing_job]),  # first poll
            MagicMock(data=[completed_job]),   # second poll
        ]
        db_mock, execute_mock = make_supabase_mock()
        execute_mock.side_effect = execute_results

        with patch("app.db.postgres_client._client", db_mock):
            with patch("app.api.routes.jobs.POLL_INTERVAL", 0):
                test_client = TestClient(app)
                response = test_client.get("/jobs/job-123/stream")

        events = _parse_sse_events(response.text)
        assert len(events) == 2
        assert events[0]["status"] == "processing"
        assert events[1]["status"] == "completed"

    def test_sse_raw_format_contains_data_prefix(self):
        check_data = [{"id": "job-123"}]
        execute_results = [
            MagicMock(data=check_data),
            MagicMock(data=[JOB_DATA]),
        ]
        db_mock, execute_mock = make_supabase_mock()
        execute_mock.side_effect = execute_results

        with patch("app.db.postgres_client._client", db_mock):
            with patch("app.api.routes.jobs.POLL_INTERVAL", 0):
                test_client = TestClient(app)
                response = test_client.get("/jobs/job-123/stream")

        # Verify raw SSE format: "data: {...}\n\n"
        data_lines = [l for l in response.text.splitlines() if l.strip().startswith("data:")]
        assert len(data_lines) >= 1
        # Each data line must be parseable JSON after stripping "data: "
        for line in data_lines:
            payload = line[len("data:"):].strip()
            parsed = json.loads(payload)
            assert isinstance(parsed, dict)
