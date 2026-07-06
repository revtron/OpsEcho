# OpsEcho - Operational Memory Platform

OpsEcho collects, normalizes, enriches, and explains infrastructure events from multiple sources (Kubernetes, Terraform, Git, CI/CD, Docker, AWS). It provides a unified timeline with AI-powered natural-language summaries and semantic search.

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Frontend**: Next.js 14 + Tailwind CSS
- **AI**: Ollama (Mistral 7B) for local LLM summaries
- **Container**: Docker Compose

## Quick Start

### Using Docker (recommended)

```bash
docker-compose up --build
```

- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Without Docker

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend (in another terminal)
cd frontend
npm install
npm run dev

# Or run the demo script
python demo.py
```

## Architecture

1. **Collectors** - Ingest events from K8s, Terraform, Git, CI/CD, Docker, AWS
2. **Normalization** - Convert raw events into a common schema
3. **Context Engine** - Enrich events with deployment history, dependencies, ownership, patterns, correlations
4. **AI Layer** - Generate operational summaries and answer questions via Ollama
5. **API** - REST endpoints for events, timeline, and semantic search

## Project Structure

```
OpsEcho/
├── backend/
│   ├── api/              # FastAPI routers (events, search, timeline)
│   ├── db/               # SQLAlchemy models and database config
│   ├── collectors/       # Event collectors (k8s, terraform, git, aws)
│   ├── context_engine/   # Event enrichment logic
│   ├── normalization/    # Event normalization
│   └── ai_layer/         # LLM-based summarization and QA
├── frontend/
│   ├── pages/            # Next.js pages
│   └── components/       # React components
├── docker-compose.yml    # Docker Compose configuration
└── demo.py               # Demo script (no external services needed)
```

## Configuration

Copy `.env.example` to `.env` and configure:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `sqlite:///./opscho.db` | PostgreSQL connection string |
| `OLLAMA_URL` | No | `http://ollama:11434` | Ollama LLM server URL |
| `GITHUB_TOKEN` | No | - | GitHub API token for webhook collector |
| `AWS_ACCESS_KEY_ID` | No | - | AWS credentials for EC2 collector |
| `AWS_SECRET_ACCESS_KEY` | No | - | AWS credentials for EC2 collector |
| `AWS_DEFAULT_REGION` | No | `us-east-1` | AWS region |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/events/{source}` | Ingest an event (k8s, terraform, git) |
| GET | `/api/timeline/` | Get event timeline |
| GET | `/api/search/` | Semantic search |
| GET | `/api/search/ask` | AI Q&A about infrastructure |
| GET | `/api/ai-status` | Check AI/Ollama status |

## Security Notes

- No secrets or API keys are committed to the repository
- The `.env` file is gitignored — use `.env.example` as a template
- Docker Compose credentials are for local development only
- AWS and GitHub tokens are optional and read from environment variables
