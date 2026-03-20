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

        # Step 2: Parse PDF into sections and extract images
        _update_job(db, job_id, "processing", "Parsing PDF sections", 20)
        from app.services.pdf_parser import parse_pdf
        parsed = parse_pdf(pdf_bytes)

        # Upload extracted images to R2
        paper_hash = hashlib.sha256(pdf_bytes).hexdigest()
        image_urls = _upload_images(parsed.images, paper_hash)

        # For PDF path, fetch paper metadata from DB (arXiv path has it in memory)
        if source_type == "pdf":
            row = db.table("papers").select("title,abstract,authors").eq("id", paper_id).execute()
            metadata = row.data[0] if row.data else {}

        # Step 3: AI extraction
        from app.services.extraction_pipeline import (
            extract_structure,
            extract_entities,
            extract_relationships_and_reasoning,
        )
        from app.services.pdf_parser import extract_structure_from_pdf
        from app.models.extraction import PaperRelationships, PaperReasoningFlow
        from app.services.graph_writer import (
            cache_llm_output,
            write_edges,
            write_nodes,
            write_reasoning_nodes,
        )

        # Step 3a: Extract structure (PDF-native first, LLM fallback)
        _update_job(db, job_id, "processing", "Extracting structure", 35)
        structure = extract_structure_from_pdf(pdf_bytes, metadata)
        if structure is None:
            structure = extract_structure(parsed, metadata)
        cache_llm_output(db, paper_id, "structure", structure.model_dump())

        # Step 3b: Extract entities
        _update_job(db, job_id, "processing", "Extracting entities", 55)
        entities = extract_entities(parsed, structure)
        cache_llm_output(db, paper_id, "entities", entities.model_dump())

        # Step 3c: Extract relationships + reasoning flow (single call)
        _update_job(db, job_id, "processing", "Extracting relationships", 80)
        combined = extract_relationships_and_reasoning(entities, structure)
        relationships = PaperRelationships(relationships=combined.relationships)
        flow = PaperReasoningFlow(steps=combined.reasoning_steps)
        cache_llm_output(db, paper_id, "relationships", relationships.model_dump())
        cache_llm_output(db, paper_id, "reasoning_flow", flow.model_dump())

        # Persist graph to DB
        node_map = write_nodes(db, paper_id, entities, image_urls=image_urls)
        write_edges(db, paper_id, relationships, node_map)
        write_reasoning_nodes(db, paper_id, flow, node_map)

        # Mark complete
        _update_job(db, job_id, "completed", "Done", 100)
        _update_paper(db, paper_id, ingestion_status="completed")

    except Exception as exc:
        _update_job(db, job_id, "failed", "Failed", 0, error=str(exc))
        _update_paper(db, paper_id, ingestion_status="failed")
        raise


def _upload_images(images, paper_hash: str) -> dict[str, str]:
    """
    Upload extracted images to R2 and return a mapping of
    label (e.g. 'Figure 1') -> R2 object key.

    Since we cannot know which image corresponds to which figure label
    from the PDF alone, we map by page-order index: 'Figure 1', 'Figure 2', etc.
    The LLM entity extraction labels figures the same way.
    """
    from app.services.storage import upload_image

    keys: dict[str, str] = {}
    for i, img in enumerate(images):
        r2_key = upload_image(
            img.image_bytes, paper_hash, img.page_number, img.image_index, img.ext
        )
        # Map by ordinal figure label and by page-based key
        label = f"Figure {i + 1}"
        keys[label] = r2_key
        # Also store by page-index key for flexible matching
        keys[f"p{img.page_number}_i{img.image_index}"] = r2_key
    return keys


async def _fetch_arxiv(arxiv_id: str):
    from app.services.arxiv_client import fetch_arxiv_pdf
    return await fetch_arxiv_pdf(arxiv_id)
