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


def upload_image(image_bytes: bytes, paper_sha256: str, page: int, index: int, ext: str) -> str:
    """
    Upload an extracted image to R2.
    Returns the R2 object key.
    """
    key = f"images/{paper_sha256}/p{page}_i{index}.{ext}"
    content_type = f"image/{ext}" if ext != "jpg" else "image/jpeg"
    client = get_r2_client()
    client.put_object(
        Bucket=settings.r2_bucket_name,
        Key=key,
        Body=image_bytes,
        ContentType=content_type,
    )
    return key


def presign_url(r2_key: str, expires_in: int = 3600) -> str:
    """
    Generate a presigned GET URL for an R2 object.
    Default expiry is 1 hour.
    """
    client = get_r2_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.r2_bucket_name, "Key": r2_key},
        ExpiresIn=expires_in,
    )
