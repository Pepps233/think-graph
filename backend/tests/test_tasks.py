"""Unit tests for workers.tasks.ingest_paper and helper functions."""

import hashlib
from contextlib import ExitStack
from unittest.mock import MagicMock, call, patch

import pytest

from tests.conftest import make_supabase_mock
from workers.tasks import _update_job, _update_paper, ingest_paper


# Patch targets for extraction -- all imported lazily inside tasks.py
_EXTRACTION_PATCHES = [
    ("app.services.pdf_parser.extract_structure_from_pdf", MagicMock(return_value=None)),
    ("app.services.extraction_pipeline.extract_structure", MagicMock()),
    ("app.services.extraction_pipeline.extract_entities", MagicMock()),
    ("app.services.extraction_pipeline.extract_relationships_and_reasoning", MagicMock()),
    ("app.services.graph_writer.write_nodes", MagicMock(return_value={})),
    ("app.services.graph_writer.write_edges", MagicMock()),
    ("app.services.graph_writer.write_reasoning_edges", MagicMock()),
    ("app.services.graph_writer.cache_llm_output", MagicMock()),
]


def _apply_extraction_patches(stack: ExitStack) -> None:
    """Enter all extraction-related patches into an ExitStack."""
    for target, default_return in _EXTRACTION_PATCHES:
        mock = stack.enter_context(patch(target))
        mock.return_value = default_return.return_value


# ---------------------------------------------------------------------------
# Helper: _update_job
# ---------------------------------------------------------------------------

class TestUpdateJob:
    def test_basic_update(self):
        db_mock, _ = make_supabase_mock()
        _update_job(db_mock, "job-1", "processing", "Parsing sections", 20)

        db_mock.table.assert_called_with("jobs")
        query_builder = db_mock.table.return_value
        query_builder.update.assert_called_once()
        update_dict = query_builder.update.call_args.args[0]
        assert update_dict["status"] == "processing"
        assert update_dict["current_step"] == "Parsing sections"
        assert update_dict["progress"] == 20
        assert "error_message" not in update_dict

    def test_update_with_error(self):
        db_mock, _ = make_supabase_mock()
        _update_job(db_mock, "job-1", "failed", "Failed", 0, error="Something broke")

        query_builder = db_mock.table.return_value
        update_dict = query_builder.update.call_args.args[0]
        assert update_dict["error_message"] == "Something broke"

    def test_eq_called_with_job_id(self):
        db_mock, _ = make_supabase_mock()
        _update_job(db_mock, "job-abc", "completed", "Done", 100)

        query_builder = db_mock.table.return_value
        query_builder.eq.assert_called_with("id", "job-abc")


# ---------------------------------------------------------------------------
# Helper: _update_paper
# ---------------------------------------------------------------------------

class TestUpdatePaper:
    def test_updates_correct_table(self):
        db_mock, _ = make_supabase_mock()
        _update_paper(db_mock, "paper-1", ingestion_status="completed")

        db_mock.table.assert_called_with("papers")

    def test_passes_kwargs_as_update(self):
        db_mock, _ = make_supabase_mock()
        _update_paper(db_mock, "paper-1", title="My Title", ingestion_status="processing")

        query_builder = db_mock.table.return_value
        update_dict = query_builder.update.call_args.args[0]
        assert update_dict["title"] == "My Title"
        assert update_dict["ingestion_status"] == "processing"

    def test_eq_called_with_paper_id(self):
        db_mock, _ = make_supabase_mock()
        _update_paper(db_mock, "paper-xyz", ingestion_status="failed")

        query_builder = db_mock.table.return_value
        query_builder.eq.assert_called_with("id", "paper-xyz")


# ---------------------------------------------------------------------------
# ingest_paper task — arXiv path
# ---------------------------------------------------------------------------

class TestIngestPaperArxiv:
    def _run_arxiv_task(self, db_mock, pdf_bytes=b"fake-pdf", metadata=None):
        if metadata is None:
            metadata = {
                "title": "Test Paper",
                "abstract": "Abstract text",
                "authors": ["Author One"],
                "doi": "10.1234/x",
                "source_url": "https://arxiv.org/pdf/2301.00001",
            }
        with ExitStack() as stack:
            stack.enter_context(patch("app.db.postgres_client._client", db_mock))
            mock_fetch = stack.enter_context(patch("workers.tasks._fetch_arxiv"))
            mock_upload = stack.enter_context(
                patch("app.services.storage.upload_pdf", return_value="pdfs/hash.pdf")
            )
            mock_parse = stack.enter_context(
                patch("app.services.pdf_parser.parse_pdf", return_value=MagicMock())
            )
            _apply_extraction_patches(stack)

            async def fake_fetch(arxiv_id):
                return pdf_bytes, metadata

            mock_fetch.side_effect = fake_fetch
            ingest_paper.apply(
                kwargs={
                    "job_id": "job-1",
                    "paper_id": "paper-1",
                    "source": "2301.00001",
                    "source_type": "arxiv",
                }
            )
        return mock_upload, mock_parse

    def test_happy_path_no_exception(self):
        db_mock, _ = make_supabase_mock()
        # Should not raise
        self._run_arxiv_task(db_mock)

    def test_final_job_status_completed(self):
        db_mock, _ = make_supabase_mock()
        with ExitStack() as stack:
            stack.enter_context(patch("app.db.postgres_client._client", db_mock))
            mock_fetch = stack.enter_context(patch("workers.tasks._fetch_arxiv"))
            stack.enter_context(patch("app.services.storage.upload_pdf", return_value="pdfs/hash.pdf"))
            stack.enter_context(patch("app.services.pdf_parser.parse_pdf", return_value=MagicMock()))
            _apply_extraction_patches(stack)

            async def fake_fetch(arxiv_id):
                return b"pdf", {"title": "T", "abstract": "A", "authors": [], "doi": None, "source_url": "u"}

            mock_fetch.side_effect = fake_fetch
            ingest_paper.apply(
                kwargs={
                    "job_id": "job-1",
                    "paper_id": "paper-1",
                    "source": "2301.00001",
                    "source_type": "arxiv",
                }
            )

        # Check last update call on jobs table had status=completed
        query_builder = db_mock.table.return_value
        all_update_calls = query_builder.update.call_args_list
        last_job_update = None
        for c in all_update_calls:
            d = c.args[0]
            if "status" in d:
                last_job_update = d
        assert last_job_update is not None
        assert last_job_update["status"] == "completed"

    def test_upload_pdf_called_with_sha256_of_bytes(self):
        pdf_bytes = b"real-pdf-content"
        db_mock, _ = make_supabase_mock()

        with ExitStack() as stack:
            stack.enter_context(patch("app.db.postgres_client._client", db_mock))
            mock_fetch = stack.enter_context(patch("workers.tasks._fetch_arxiv"))
            mock_upload = stack.enter_context(
                patch("app.services.storage.upload_pdf", return_value="pdfs/hash.pdf")
            )
            stack.enter_context(patch("app.services.pdf_parser.parse_pdf", return_value=MagicMock()))
            _apply_extraction_patches(stack)

            async def fake_fetch(arxiv_id):
                return pdf_bytes, {"title": "T", "abstract": "A", "authors": [], "doi": None, "source_url": "u"}

            mock_fetch.side_effect = fake_fetch
            ingest_paper.apply(
                kwargs={
                    "job_id": "job-1",
                    "paper_id": "paper-1",
                    "source": "2301.00001",
                    "source_type": "arxiv",
                }
            )

        expected_sha = hashlib.sha256(pdf_bytes).hexdigest()
        mock_upload.assert_called_once_with(pdf_bytes, expected_sha)

    def test_progress_updates_in_order(self):
        db_mock, _ = make_supabase_mock()

        with ExitStack() as stack:
            stack.enter_context(patch("app.db.postgres_client._client", db_mock))
            mock_fetch = stack.enter_context(patch("workers.tasks._fetch_arxiv"))
            stack.enter_context(patch("app.services.storage.upload_pdf", return_value="pdfs/hash.pdf"))
            stack.enter_context(patch("app.services.pdf_parser.parse_pdf", return_value=MagicMock()))
            _apply_extraction_patches(stack)

            async def fake_fetch(arxiv_id):
                return b"pdf", {"title": "T", "abstract": "A", "authors": [], "doi": None, "source_url": "u"}

            mock_fetch.side_effect = fake_fetch
            ingest_paper.apply(
                kwargs={
                    "job_id": "job-1",
                    "paper_id": "paper-1",
                    "source": "2301.00001",
                    "source_type": "arxiv",
                }
            )

        query_builder = db_mock.table.return_value
        progress_values = [
            c.args[0]["progress"]
            for c in query_builder.update.call_args_list
            if "progress" in c.args[0]
        ]
        expected = [5, 20, 35, 55, 80, 100]
        assert progress_values == expected

    def test_exception_marks_job_failed(self):
        db_mock, _ = make_supabase_mock()

        with (
            patch("app.db.postgres_client._client", db_mock),
            patch("workers.tasks._fetch_arxiv") as mock_fetch,
            patch("app.services.storage.upload_pdf"),
            patch("app.services.pdf_parser.parse_pdf"),
        ):
            async def fail_fetch(arxiv_id):
                raise ValueError("Network error")

            mock_fetch.side_effect = fail_fetch

            with pytest.raises(ValueError):
                ingest_paper.apply(
                    kwargs={
                        "job_id": "job-1",
                        "paper_id": "paper-1",
                        "source": "2301.00001",
                        "source_type": "arxiv",
                    }
                )

        query_builder = db_mock.table.return_value
        failed_updates = [
            c.args[0]
            for c in query_builder.update.call_args_list
            if c.args[0].get("status") == "failed"
        ]
        assert len(failed_updates) >= 1
        assert "error_message" in failed_updates[0]
        assert failed_updates[0]["error_message"] == "Network error"

    def test_exception_marks_paper_failed(self):
        db_mock, _ = make_supabase_mock()

        with (
            patch("app.db.postgres_client._client", db_mock),
            patch("workers.tasks._fetch_arxiv") as mock_fetch,
        ):
            async def fail_fetch(arxiv_id):
                raise RuntimeError("fetch failed")

            mock_fetch.side_effect = fail_fetch

            with pytest.raises(RuntimeError):
                ingest_paper.apply(
                    kwargs={
                        "job_id": "job-1",
                        "paper_id": "paper-1",
                        "source": "2301.00001",
                        "source_type": "arxiv",
                    }
                )

        query_builder = db_mock.table.return_value
        paper_failed = any(
            c.args[0].get("ingestion_status") == "failed"
            for c in query_builder.update.call_args_list
        )
        assert paper_failed


# ---------------------------------------------------------------------------
# ingest_paper task — PDF path
# ---------------------------------------------------------------------------

class TestIngestPaperPdf:
    def test_happy_path_no_exception(self):
        pdf_bytes = b"uploaded-pdf-data"
        db_mock, _ = make_supabase_mock()

        with ExitStack() as stack:
            stack.enter_context(patch("app.db.postgres_client._client", db_mock))
            stack.enter_context(patch("app.services.storage.download_pdf", return_value=pdf_bytes))
            stack.enter_context(patch("app.services.pdf_parser.parse_pdf", return_value=MagicMock()))
            _apply_extraction_patches(stack)
            ingest_paper.apply(
                kwargs={
                    "job_id": "job-2",
                    "paper_id": "paper-2",
                    "source": "pdfs/myhash.pdf",
                    "source_type": "pdf",
                }
            )

        # Should reach completed status
        query_builder = db_mock.table.return_value
        completed = any(
            c.args[0].get("status") == "completed"
            for c in query_builder.update.call_args_list
        )
        assert completed

    def test_download_pdf_called_with_r2_key(self):
        r2_key = "pdfs/myhash.pdf"
        db_mock, _ = make_supabase_mock()

        with ExitStack() as stack:
            stack.enter_context(patch("app.db.postgres_client._client", db_mock))
            mock_download = stack.enter_context(
                patch("app.services.storage.download_pdf", return_value=b"data")
            )
            stack.enter_context(patch("app.services.pdf_parser.parse_pdf", return_value=MagicMock()))
            _apply_extraction_patches(stack)
            ingest_paper.apply(
                kwargs={
                    "job_id": "job-2",
                    "paper_id": "paper-2",
                    "source": r2_key,
                    "source_type": "pdf",
                }
            )

        mock_download.assert_called_once_with(r2_key)


# ---------------------------------------------------------------------------
# PDF structure fallback logic
# ---------------------------------------------------------------------------

class TestPdfStructureFallback:
    def _run_with_pdf_structure(self, pdf_structure_return):
        """Run ingestion with a controlled extract_structure_from_pdf return value."""
        db_mock, _ = make_supabase_mock()

        with ExitStack() as stack:
            stack.enter_context(patch("app.db.postgres_client._client", db_mock))
            mock_fetch = stack.enter_context(patch("workers.tasks._fetch_arxiv"))
            stack.enter_context(patch("app.services.storage.upload_pdf", return_value="pdfs/hash.pdf"))
            stack.enter_context(patch("app.services.pdf_parser.parse_pdf", return_value=MagicMock()))

            mock_pdf_struct = stack.enter_context(
                patch("app.services.pdf_parser.extract_structure_from_pdf", return_value=pdf_structure_return)
            )
            mock_llm_struct = stack.enter_context(
                patch("app.services.extraction_pipeline.extract_structure", return_value=MagicMock())
            )
            stack.enter_context(patch("app.services.extraction_pipeline.extract_entities", return_value=MagicMock()))
            stack.enter_context(patch("app.services.extraction_pipeline.extract_relationships_and_reasoning", return_value=MagicMock()))
            stack.enter_context(patch("app.services.graph_writer.write_nodes", return_value={}))
            stack.enter_context(patch("app.services.graph_writer.write_edges"))
            stack.enter_context(patch("app.services.graph_writer.write_reasoning_edges"))
            stack.enter_context(patch("app.services.graph_writer.cache_llm_output"))

            async def fake_fetch(arxiv_id):
                return b"pdf", {"title": "T", "abstract": "A", "authors": [], "doi": None, "source_url": "u"}

            mock_fetch.side_effect = fake_fetch
            ingest_paper.apply(
                kwargs={
                    "job_id": "job-1",
                    "paper_id": "paper-1",
                    "source": "2301.00001",
                    "source_type": "arxiv",
                }
            )

        return mock_pdf_struct, mock_llm_struct

    def test_pdf_structure_none_falls_back_to_llm(self):
        _, mock_llm = self._run_with_pdf_structure(None)
        mock_llm.assert_called_once()

    def test_pdf_structure_success_skips_llm(self):
        from app.models.extraction import PaperStructure, SectionInfo
        fake_structure = PaperStructure(
            title="T", abstract="A", authors=[],
            sections=[
                SectionInfo(section_number="1", section_name="Intro", page_start=1),
                SectionInfo(section_number="2", section_name="Methods", page_start=2),
            ]
        )
        _, mock_llm = self._run_with_pdf_structure(fake_structure)
        mock_llm.assert_not_called()


# ---------------------------------------------------------------------------
# PaperRelationshipsAndReasoning model
# ---------------------------------------------------------------------------

class TestPaperRelationshipsAndReasoningModel:
    def test_instantiation_and_split(self):
        from app.models.extraction import (
            PaperRelationshipsAndReasoning,
            PaperRelationships,
            PaperReasoningFlow,
            Relationship,
            RelationshipType,
            ReasoningStep,
        )

        combined = PaperRelationshipsAndReasoning(
            relationships=[
                Relationship(
                    source_title="Method A",
                    target_title="Result B",
                    relationship_type=RelationshipType.PRODUCES_RESULT,
                )
            ],
            reasoning_steps=[
                ReasoningStep(
                    entity_title="Method A",
                )
            ],
        )

        rels = PaperRelationships(relationships=combined.relationships)
        flow = PaperReasoningFlow(steps=combined.reasoning_steps)

        assert len(rels.relationships) == 1
        assert rels.relationships[0].source_title == "Method A"
        assert len(flow.steps) == 1
        assert flow.steps[0].entity_title == "Method A"

    def test_empty_instantiation(self):
        from app.models.extraction import PaperRelationshipsAndReasoning

        combined = PaperRelationshipsAndReasoning()
        assert combined.relationships == []
        assert combined.reasoning_steps == []
