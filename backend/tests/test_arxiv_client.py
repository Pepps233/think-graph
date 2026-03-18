"""Async unit tests for app.services.arxiv_client."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.arxiv_client import fetch_arxiv_pdf


def _make_arxiv_paper(arxiv_id: str = "2301.00001"):
    """Build a fake arxiv.Result-like namespace."""
    return SimpleNamespace(
        title="Test Paper Title",
        summary="This is the abstract.",
        authors=[
            SimpleNamespace(name="Alice Smith"),
            SimpleNamespace(name="Bob Jones"),
        ],
        doi="10.1234/test.doi",
        pdf_url=f"https://arxiv.org/pdf/{arxiv_id}",
    )


class TestFetchArxivPdf:
    async def test_happy_path_returns_bytes_and_metadata(self):
        paper = _make_arxiv_paper()
        pdf_content = b"fake-pdf-bytes"

        mock_http_response = MagicMock()
        mock_http_response.content = pdf_content
        mock_http_response.raise_for_status = MagicMock()

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_http_response)
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("app.services.arxiv_client.arxiv.Client") as mock_arxiv_client_cls,
            patch("app.services.arxiv_client.httpx.AsyncClient", return_value=mock_http_client),
        ):
            instance = mock_arxiv_client_cls.return_value
            instance.results.return_value = iter([paper])

            result_bytes, metadata = await fetch_arxiv_pdf("2301.00001")

        assert result_bytes == pdf_content
        assert metadata["title"] == "Test Paper Title"
        assert metadata["abstract"] == "This is the abstract."
        assert metadata["authors"] == ["Alice Smith", "Bob Jones"]
        assert metadata["arxiv_id"] == "2301.00001"
        assert metadata["doi"] == "10.1234/test.doi"
        assert "source_url" in metadata

    async def test_authors_is_list_of_strings(self):
        paper = _make_arxiv_paper()
        mock_http_response = MagicMock(content=b"pdf", raise_for_status=MagicMock())
        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_http_response)
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("app.services.arxiv_client.arxiv.Client") as mock_arxiv_client_cls,
            patch("app.services.arxiv_client.httpx.AsyncClient", return_value=mock_http_client),
        ):
            instance = mock_arxiv_client_cls.return_value
            instance.results.return_value = iter([paper])
            _, metadata = await fetch_arxiv_pdf("2301.00001")

        assert isinstance(metadata["authors"], list)
        assert all(isinstance(a, str) for a in metadata["authors"])

    async def test_arxiv_id_not_found_raises_value_error(self):
        with patch("app.services.arxiv_client.arxiv.Client") as mock_arxiv_client_cls:
            instance = mock_arxiv_client_cls.return_value
            instance.results.return_value = iter([])

            with pytest.raises(ValueError, match="arXiv paper not found"):
                await fetch_arxiv_pdf("9999.99999")

    async def test_http_error_propagates(self):
        paper = _make_arxiv_paper()
        mock_http_response = MagicMock()
        mock_http_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=MagicMock()
        )

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_http_response)
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("app.services.arxiv_client.arxiv.Client") as mock_arxiv_client_cls,
            patch("app.services.arxiv_client.httpx.AsyncClient", return_value=mock_http_client),
        ):
            instance = mock_arxiv_client_cls.return_value
            instance.results.return_value = iter([paper])

            with pytest.raises(httpx.HTTPStatusError):
                await fetch_arxiv_pdf("2301.00001")

    async def test_httpx_timeout_propagates(self):
        paper = _make_arxiv_paper()

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("app.services.arxiv_client.arxiv.Client") as mock_arxiv_client_cls,
            patch("app.services.arxiv_client.httpx.AsyncClient", return_value=mock_http_client),
        ):
            instance = mock_arxiv_client_cls.return_value
            instance.results.return_value = iter([paper])

            with pytest.raises(httpx.TimeoutException):
                await fetch_arxiv_pdf("2301.00001")

    async def test_arxiv_id_with_path_prefix_is_cleaned(self):
        """'abs/2301.00001v2' should resolve to clean_id '2301.00001v2'."""
        paper = _make_arxiv_paper("2301.00001v2")
        mock_http_response = MagicMock(content=b"pdf", raise_for_status=MagicMock())
        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_http_response)
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("app.services.arxiv_client.arxiv.Client") as mock_arxiv_client_cls,
            patch("app.services.arxiv_client.httpx.AsyncClient", return_value=mock_http_client),
        ):
            instance = mock_arxiv_client_cls.return_value
            instance.results.return_value = iter([paper])

            _, metadata = await fetch_arxiv_pdf("abs/2301.00001v2")

        assert metadata["arxiv_id"] == "2301.00001v2"
