import arxiv
import httpx
from pathlib import Path
import tempfile


async def fetch_arxiv_pdf(arxiv_id: str) -> tuple[bytes, dict]:
    """
    Download PDF and extract metadata for a given arXiv ID.
    Returns (pdf_bytes, metadata_dict).
    """
    clean_id = arxiv_id.strip().split("/")[-1]

    client = arxiv.Client()
    search = arxiv.Search(id_list=[clean_id])
    results = list(client.results(search))

    if not results:
        raise ValueError(f"arXiv paper not found: {clean_id}")

    paper = results[0]
    pdf_url = paper.pdf_url

    async with httpx.AsyncClient(follow_redirects=True, timeout=60) as http:
        response = await http.get(pdf_url)
        response.raise_for_status()
        pdf_bytes = response.content

    metadata = {
        "title": paper.title,
        "abstract": paper.summary,
        "authors": [a.name for a in paper.authors],
        "arxiv_id": clean_id,
        "doi": paper.doi,
        "source_url": pdf_url,
    }

    return pdf_bytes, metadata
