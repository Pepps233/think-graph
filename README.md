# ThinkGraph AI

https://github.com/user-attachments/assets/9dd39d02-2c83-489b-84fe-1b743f6ae387

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

## Testing

### Backend

Install test dependencies, then run pytest:

```bash
cd backend
pip install -r requirements-dev.txt
pytest --tb=short
```

Run a specific test file:

```bash
pytest tests/test_pdf_parser.py -v
pytest tests/test_routes_jobs.py -v -k stream
```

Generate a coverage report:

```bash
pytest --cov=app --cov=workers --cov-report=html
open htmlcov/index.html
```

### Frontend

```bash
cd frontend
npx vitest run
```

Run in watch mode during development:

```bash
npx vitest
```

### CI

Tests run automatically on every push and on pull requests targeting `main` via GitHub Actions (`.github/workflows/ci.yml`). Both the backend (pytest) and frontend (Vitest) jobs must pass before a PR can be merged.

---

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

## 1. Start the FastAPI server

```
cd backend
source .venv313/bin/activate
uvicorn app.main:app --reload --port 8000
```

## 2. Start the Celery worker (separate terminal)

```
cd backend
source .venv313/bin/activate
celery -A workers.celery_app worker --loglevel=info
```

## 3. Start the frontend (separate terminal)

```
cd frontend
npm run dev
```

Then open http://localhost:3000.
