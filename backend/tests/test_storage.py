"""Unit tests for app.services.storage — boto3 fully mocked."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.storage import download_pdf, upload_pdf


class TestUploadPdf:
    def test_returns_correct_key(self):
        sha256 = "abc123"
        mock_client = MagicMock()

        with patch("app.services.storage.boto3.client", return_value=mock_client):
            key = upload_pdf(b"pdf-bytes", sha256)

        assert key == f"pdfs/{sha256}.pdf"

    def test_put_object_called_with_correct_args(self):
        sha256 = "deadbeef"
        pdf_bytes = b"hello pdf"
        mock_client = MagicMock()

        with patch("app.services.storage.boto3.client", return_value=mock_client):
            from app.config import settings
            upload_pdf(pdf_bytes, sha256)

        mock_client.put_object.assert_called_once_with(
            Bucket=settings.r2_bucket_name,
            Key=f"pdfs/{sha256}.pdf",
            Body=pdf_bytes,
            ContentType="application/pdf",
        )


class TestDownloadPdf:
    def test_returns_bytes(self):
        expected_bytes = b"downloaded pdf content"
        mock_body = MagicMock()
        mock_body.read.return_value = expected_bytes

        mock_client = MagicMock()
        mock_client.get_object.return_value = {"Body": mock_body}

        with patch("app.services.storage.boto3.client", return_value=mock_client):
            result = download_pdf("pdfs/some-key.pdf")

        assert result == expected_bytes

    def test_get_object_called_with_correct_args(self):
        mock_body = MagicMock()
        mock_body.read.return_value = b"data"
        mock_client = MagicMock()
        mock_client.get_object.return_value = {"Body": mock_body}

        r2_key = "pdfs/myhash.pdf"

        with patch("app.services.storage.boto3.client", return_value=mock_client):
            from app.config import settings
            download_pdf(r2_key)

        mock_client.get_object.assert_called_once_with(
            Bucket=settings.r2_bucket_name,
            Key=r2_key,
        )
