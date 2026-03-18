# ThinkGraph AI

An AI-powered platform that converts academic research papers into interactive knowledge graphs. Paste an arXiv URL or upload a PDF and instantly explore the paper's concepts, methods, citations, and reasoning as a navigable visual graph.

## Features

- **PDF & arXiv ingestion** — upload a PDF or paste an arXiv link
- **AI extraction pipeline** — GPT-4o extracts entities, relationships, and reasoning flow in 4 structured passes
- **Interactive knowledge graph** — zoom, pan, expand nodes, and trace connections visually
- **Source provenance** — every node links back to its exact section, page, and label (e.g. "Equation 6a") in the original paper
- **Graph chat** — converse with an LLM that can traverse graph nodes; ping any node to feed it as context
- **Multi-paper comparison** — load multiple papers and explore shared concepts and method evolution
- **Citation expansion** — expand citation nodes to ingest referenced papers on demand

## Tech Stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui |
| Graph visualization | React Flow v11 |
| Equation rendering | KaTeX |
| Backend | FastAPI (Python 3.12) |
| AI extraction | GPT-4o + instructor |
| Database | PostgreSQL 16 (Supabase) |
| Object storage | Cloudflare R2 |
| Job queue | Celery + Upstash Redis |

## Project Structure

```
thinkgraph/
├── frontend/       # Next.js 14 app
└── backend/        # FastAPI + Celery workers
```

## Getting Started

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Celery Worker

```bash
cd backend
celery -A workers.celery_app worker --loglevel=info
```

## Environment Variables

Copy `.env.example` and fill in your keys:

```
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
OPENAI_API_KEY
R2_ACCESS_KEY_ID
R2_SECRET_ACCESS_KEY
R2_S3_ENDPOINT
CELERY_BROKER_URL
```
