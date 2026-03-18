import asyncio
import hashlib

from workers.celery_app import celery_app


def _update_job(db, job_id: str, status: str, step: str, progress: int, error: str = None):
    update = {"status": status, "current_step": step, "progress": progress}
    if error:
        update["error_message"] = error
    db.table("jobs").update(update).eq("id", job_id).execute()


def _update_paper(db, paper_id: str, **kwargs):
    db.table("papers").update(kwargs).eq("id", paper_id).execute()


@celery_app.task(bind=True, name="workers.tasks.ingest_paper")
def ingest_paper(self, job_id: str, paper_id: str, source: str, source_type: str):
    """
    Main ingestion task.
    source: arXiv ID (source_type='arxiv') or R2 key (source_type='pdf')
    """
    from app.db.postgres_client import get_client

    db = get_client()

    try:
        # Step 1: Download / retrieve PDF
        _update_job(db, job_id, "processing", "Downloading PDF", 5)

        if source_type == "arxiv":
            pdf_bytes, metadata = asyncio.run(_fetch_arxiv(source))
            sha256 = hashlib.sha256(pdf_bytes).hexdigest()

            from app.services.storage import upload_pdf
            r2_key = upload_pdf(pdf_bytes, sha256)

            _update_paper(
                db,
                paper_id,
                title=metadata["title"],
                abstract=metadata["abstract"],
                authors=metadata["authors"],
                doi=metadata.get("doi"),
                sha256_hash=sha256,
                r2_pdf_key=r2_key,
                ingestion_status="processing",
            )
        else:
            # PDF already uploaded — download from R2 for parsing
            from app.services.storage import download_pdf
            pdf_bytes = download_pdf(source)
            _update_paper(db, paper_id, ingestion_status="processing")

        # Step 2: Parse PDF into sections
        _update_job(db, job_id, "processing", "Parsing PDF sections", 20)
        from app.services.pdf_parser import parse_pdf
        parsed = parse_pdf(pdf_bytes)

        # For PDF path, fetch paper metadata from DB (arXiv path has it in memory)
        if source_type == "pdf":
            row = db.table("papers").select("title,abstract,authors").eq("id", paper_id).execute()
            metadata = row.data[0] if row.data else {}

        # Step 3: AI extraction
        from app.services.extraction_pipeline import (
            extract_structure,
            extract_entities,
            extract_relationships,
            extract_reasoning_flow,
        )
        from app.services.graph_writer import (
            cache_llm_output,
            write_edges,
            write_nodes,
            write_reasoning_nodes,
        )

        _update_job(db, job_id, "processing", "Extracting structure", 35)
        structure = extract_structure(parsed, metadata)
        cache_llm_output(db, paper_id, "structure", structure.model_dump())

        _update_job(db, job_id, "processing", "Extracting entities", 50)
        entities = extract_entities(parsed, structure)
        cache_llm_output(db, paper_id, "entities", entities.model_dump())

        _update_job(db, job_id, "processing", "Extracting relationships", 70)
        relationships = extract_relationships(parsed, entities)
        cache_llm_output(db, paper_id, "relationships", relationships.model_dump())

        _update_job(db, job_id, "processing", "Extracting reasoning flow", 85)
        flow = extract_reasoning_flow(parsed, structure)
        cache_llm_output(db, paper_id, "reasoning_flow", flow.model_dump())

        # Persist graph to DB
        node_map = write_nodes(db, paper_id, entities)
        write_edges(db, paper_id, relationships, node_map)
        write_reasoning_nodes(db, paper_id, flow, node_map)

        # Mark complete
        _update_job(db, job_id, "completed", "Done", 100)
        _update_paper(db, paper_id, ingestion_status="completed")

    except Exception as exc:
        _update_job(db, job_id, "failed", "Failed", 0, error=str(exc))
        _update_paper(db, paper_id, ingestion_status="failed")
        raise


async def _fetch_arxiv(arxiv_id: str):
    from app.services.arxiv_client import fetch_arxiv_pdf
    return await fetch_arxiv_pdf(arxiv_id)
