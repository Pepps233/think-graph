import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.db.postgres_client import get_client

router = APIRouter(prefix="/jobs", tags=["jobs"])

POLL_INTERVAL = 2  # seconds between DB polls while streaming


@router.get("/{job_id}")
async def get_job(job_id: str):
    """Single job status snapshot."""
    db = get_client()
    result = db.table("jobs").select("*").eq("id", job_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Job not found")
    return result.data[0]


@router.get("/{job_id}/stream")
async def stream_job(job_id: str):
    """
    SSE endpoint that streams job progress until the job reaches
    a terminal state (completed | failed).

    Each event is a JSON object:
      { id, paper_id, status, current_step, progress, error_message }
    """
    db = get_client()

    check = db.table("jobs").select("id").eq("id", job_id).execute()
    if not check.data:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        while True:
            result = db.table("jobs").select("*").eq("id", job_id).execute()
            if not result.data:
                yield _sse({"error": "Job not found"})
                break

            job = result.data[0]
            yield _sse(job)

            if job["status"] in ("completed", "failed"):
                break

            await asyncio.sleep(POLL_INTERVAL)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"
