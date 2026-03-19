import asyncio
import hashlib
import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.db.postgres_client import get_client
from workers.tasks import ingest_paper

_executor = ThreadPoolExecutor(max_workers=4)

router = APIRouter(prefix="/papers", tags=["papers"])


class IngestURLRequest(BaseModel):
    arxiv_url: str


class IngestResponse(BaseModel):
    paper_id: str
    job_id: str


@router.post("/ingest/url", response_model=IngestResponse)
async def ingest_from_url(body: IngestURLRequest):
    """Accept an arXiv URL and kick off background ingestion."""
    arxiv_id = _extract_arxiv_id(body.arxiv_url)
    if not arxiv_id:
        raise HTTPException(status_code=422, detail="Could not parse arXiv ID from URL")

    db = get_client()

    # Create paper row
    paper_id = str(uuid.uuid4())
    db.table("papers").insert({
        "id": paper_id,
        "arxiv_id": arxiv_id,
        "source_url": body.arxiv_url,
        "ingestion_status": "pending",
    }).execute()

    # Create job row
    job_id = str(uuid.uuid4())
    db.table("jobs").insert({
        "id": job_id,
        "paper_id": paper_id,
        "status": "queued",
        "current_step": "Queued",
        "progress": 0,
    }).execute()

    # Dispatch Celery task — fire and forget, don't block the response
    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        _executor,
        lambda: ingest_paper.delay(job_id=job_id, paper_id=paper_id, source=arxiv_id, source_type="arxiv"),
    )

    return IngestResponse(paper_id=paper_id, job_id=job_id)


@router.post("/ingest/pdf", response_model=IngestResponse)
async def ingest_from_pdf(file: UploadFile = File(...)):
    """Accept a PDF upload and kick off background ingestion."""
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=422, detail="File must be a PDF")

    pdf_bytes = await file.read()
    sha256 = hashlib.sha256(pdf_bytes).hexdigest()

    db = get_client()

    # Check for duplicate by hash
    existing = db.table("papers").select("id").eq("sha256_hash", sha256).execute()
    if existing.data:
        existing_paper_id = existing.data[0]["id"]
        raise HTTPException(
            status_code=409,
            detail=f"Paper already ingested: {existing_paper_id}",
        )

    # Upload PDF to R2 and create paper row
    from app.services.storage import upload_pdf
    r2_key = upload_pdf(pdf_bytes, sha256)

    paper_id = str(uuid.uuid4())
    db.table("papers").insert({
        "id": paper_id,
        "sha256_hash": sha256,
        "r2_pdf_key": r2_key,
        "ingestion_status": "pending",
    }).execute()

    # Create job row
    job_id = str(uuid.uuid4())
    db.table("jobs").insert({
        "id": job_id,
        "paper_id": paper_id,
        "status": "queued",
        "current_step": "Queued",
        "progress": 0,
    }).execute()

    # Dispatch Celery task — fire and forget, don't block the response
    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        _executor,
        lambda: ingest_paper.delay(job_id=job_id, paper_id=paper_id, source=r2_key, source_type="pdf"),
    )

    return IngestResponse(paper_id=paper_id, job_id=job_id)


@router.get("/{paper_id}")
async def get_paper(paper_id: str):
    db = get_client()
    result = db.table("papers").select("*").eq("id", paper_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Paper not found")
    return result.data[0]


def _extract_arxiv_id(url: str) -> str | None:
    """Extract arXiv ID from URLs like arxiv.org/abs/2301.00001 or arxiv.org/pdf/2301.00001."""
    import re
    match = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9]+\.[0-9]+(?:v\d+)?)", url)
    if match:
        return match.group(1)
    # Accept bare IDs like "2301.00001"
    if re.fullmatch(r"[0-9]+\.[0-9]+(v\d+)?", url.strip()):
        return url.strip()
    return None
