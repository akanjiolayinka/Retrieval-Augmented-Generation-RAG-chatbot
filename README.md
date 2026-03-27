# DocuMind AI

Portfolio-grade Retrieval-Augmented Generation (RAG) chatbot focused on backend engineering quality and practical AI system design.

## 1) Recommended Stack (Internship-Ready)

### Backend and API
- Python 3.12
- FastAPI (typed, async-first, production-friendly)
- Uvicorn (ASGI server)
- Pydantic Settings (strong config validation)

### Data Layer
- PostgreSQL 16
- pgvector (vector similarity inside Postgres)
- SQLAlchemy 2.0 + Alembic migrations

### AI and Retrieval
- OpenAI Embeddings + Chat Completions
- In-house retrieval pipeline (clean, explainable service boundaries)
- Optional reranker later (Cohere/Jina/Cross-Encoder)

### Infra and DX
- Docker Compose for local services
- Pytest for testing
- Ruff + mypy for code quality
- Structured logging for observability

Why this stack is strong for internships:
- Shows real backend patterns (layers, config, validation, error boundaries)
- Shows practical AI integration without hiding everything behind a framework
- Shows production-minded engineering with testing and local reproducibility

## 2) Project Structure (Clean and Scalable)

```text
.
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── router.py
│   │       └── routes/
│   │           ├── health.py
│   │           ├── documents.py          # later
│   │           ├── chat.py               # later
│   │           └── auth.py               # later
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── security.py                   # later
│   ├── db/
│   │   ├── session.py                    # later
│   │   ├── base.py                       # later
│   │   └── models/                       # later
│   ├── schemas/
│   │   └── health.py
│   ├── services/                         # later
│   │   ├── ingestion/
│   │   ├── embeddings/
│   │   ├── retrieval/
│   │   └── chat/


│   ├── workers/                          # later (background indexing)
│   └── main.py
├── tests/
│   ├── test_health.py
│   └── integration/                      # later
├── .env.example
├── docker-compose.yml
├── pyproject.toml
└── Makefile
```

## 3) Milestones

### MVP
1. FastAPI backend foundation with health checks and config
2. Document upload endpoint (PDF/TXT)
3. Text extraction + cleaning + chunking
4. Embedding generation and pgvector storage
5. Query endpoint: retrieve chunks + answer with citations

### Standout Version
1. Hybrid retrieval (vector + keyword)
2. Reranking layer for higher answer quality
3. Streaming responses
4. Rate limits + audit logging
5. Evaluation harness (retrieval quality and answer groundedness)

## 4) End-to-End Architecture

```text
Client
	-> POST /documents/upload
			-> Document Service
			-> Parser (PDF/TXT)
			-> Text Cleaner
			-> Chunker
			-> Embedding Service
			-> Postgres + pgvector (chunks + vectors + metadata)

Client
	-> POST /chat/ask
			-> Question Embedding
			-> Retrieval Service (similarity search)
			-> Prompt Builder (context + guardrails)
			-> LLM Service (answer generation)
			-> Save chat message + sources
			-> Return answer + citations
```

Key storage split:
- Relational tables: users, documents, chunks, chats, messages
- Vector index: chunk embeddings for semantic retrieval

## 5) Step 1 (Implemented): Backend Foundation

### Objective
Build a production-style skeleton that we can safely extend in later milestones.

### Included
- FastAPI application setup
- Versioned API router
- Health endpoint
- Typed environment configuration
- Structured logging
- Docker Compose with PostgreSQL + pgvector
- Lint/type/test tooling config
- Basic API test

### Run Locally

1. Copy environment file:

```bash
cp .env.example .env
```

2. Start database:

```bash
docker compose up -d postgres
```

3. Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
```

4. Start API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Verify:

```bash
curl http://localhost:8000/api/v1/health
```

## 6) Step 2 (Implemented): Database + Upload Ingestion Entry Point

### Objective
Add the first real ingestion entry point that demonstrates backend design depth: API -> service -> database.

### Included
- SQLAlchemy session wiring and declarative model base
- Alembic migration setup
- `documents` metadata table migration
- `POST /api/v1/documents/upload` endpoint
- File validation (size, MIME type, extension)
- Local file persistence for uploaded binaries
- Metadata persistence in PostgreSQL
- Endpoint tests using dependency overrides and isolated SQLite test database

### Run Step 2

1. Start PostgreSQL:

```bash
docker compose up -d postgres
```

2. Apply migrations:

```bash
make db-upgrade
```

3. Start API:

```bash
make run
```

4. Upload a file:

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
	-F "file=@./README.md;type=text/plain"
```

## 7) Step 3 (Implemented): Parsing + Cleaning + Chunking Pipeline

### Objective
Turn uploaded documents into structured chunks that can be embedded and retrieved.

### Included
- Parser layer for text and PDF inputs
- Text cleaning and normalization
- Configurable chunking (`CHUNK_SIZE_CHARS`, `CHUNK_OVERLAP_CHARS`)
- `document_chunks` relational table + migration
- Ingestion status transitions:
	- `uploaded` -> `processing` -> `chunked`
	- `uploaded` -> `processing` -> `failed` (on ingestion errors)
- Upload response now includes chunk count

### Run New Migration

```bash
make db-upgrade
```

## 8) Step 4 (Implemented): Embeddings + Retrieval + Chat Ask

### Objective
Create the first full RAG query loop: embed chunks, retrieve by semantic similarity, and answer with citations.

### Included
- Embedding service with two providers:
	- `openai` for production-style embeddings
	- `local` deterministic embeddings for offline development/tests
- `document_chunks.embedding` vector column (pgvector)
- Retrieval service with PostgreSQL vector search and SQLite fallback scoring
- `POST /api/v1/chat/ask` endpoint
- LLM service with two providers:
	- `openai` for generated responses
	- `local` grounded fallback for local/dev use
- Citations in API response (`document_id`, `chunk_id`, `chunk_index`, `score`, `text`)

### Ingestion Status Flow
- `uploaded`
- `processing`
- `embedded`
- `failed`

### Run New Migration

```bash
make db-upgrade
```

### Ask a Question

```bash
curl -X POST http://localhost:8000/api/v1/chat/ask \
	-H "Content-Type: application/json" \
	-d '{"question":"What does this document say about vector search?","top_k":5}'
```

### Next Step
Add chat history persistence (sessions/messages), then connect answer generation and retrieval traces to those records for auditability and debugging.
