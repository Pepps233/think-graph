import boto3
from botocore.config import Config
from app.config import settings


def get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.r2_s3_endpoint,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def upload_pdf(pdf_bytes: bytes, sha256_hash: str) -> str:
    """
    Upload PDF to R2. Returns the R2 object key.
    Key is content-addressed by SHA256 to avoid duplicates.
    """
    key = f"pdfs/{sha256_hash}.pdf"
    client = get_r2_client()
    client.put_object(
        Bucket=settings.r2_bucket_name,
        Key=key,
        Body=pdf_bytes,
        ContentType="application/pdf",
    )
    return key


def download_pdf(r2_key: str) -> bytes:
    client = get_r2_client()
    response = client.get_object(Bucket=settings.r2_bucket_name, Key=r2_key)
    return response["Body"].read()
