from workers.celery_app import celery_app


@celery_app.task(bind=True, name="workers.tasks.ingest_paper")
def ingest_paper(self, job_id: str, paper_id: str, source: str, source_type: str):
    """
    Main ingestion task — implemented in Step 2.
    source: URL or R2 key
    source_type: 'arxiv' | 'pdf'
    """
    pass
