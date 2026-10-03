# AI-Powered Fine Print Auditor

> Autonomous legal intelligence engine designed to analyze complex Terms of Service, Privacy Policies, and EULAs to surface predatory clauses, hidden privacy risks, and unfair terms.

---

## 📌 Phase 0 Foundation Overview

Phase 0 establishes the containerized foundation and core architectural skeleton for the project. No advanced AI, RAG, chatbot, or browser extensions are active in this phase—only the verified, production-ready operational baseline.

### Key Technology Stack:
- **Backend:** Python 3.13 + FastAPI, Uvicorn
- **Database:** PostgreSQL 16 with `pgvector` vector extension
- **Database Driver:** `psycopg` (psycopg 3 binary)
- **ORM:** SQLAlchemy 2.0 (Declarative Base)
- **Database Migrations:** Alembic
- **Frontend:** React 18 + Vite, modern Vanilla CSS design system
- **Containerization:** Docker & Docker Compose
- **Modular AI Layer:** Abstract provider interface supporting OpenAI, Anthropic, Ollama, and local GGUF/Qwen models

---

## 📁 Project Directory Structure

```text
fine-print-auditor/
├── backend/
│   ├── app/
│   │   ├── api/             # API versioning & endpoint routers
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   └── health.py    # GET /health implementation
│   │   │       └── api.py
│   │   ├── core/            # Configuration (Pydantic BaseSettings)
│   │   │   └── config.py
│   │   ├── database/        # Engine, session factory & connection diagnostics
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   ├── models/          # SQLAlchemy Declarative models & mixins
│   │   │   └── base.py
│   │   ├── schemas/         # Pydantic validation schemas
│   │   │   └── health.py
│   │   ├── services/        # Business logic services (Phase 1+)
│   │   ├── extraction/      # Document ingestion & parsing (Phase 1+)
│   │   ├── analysis/        # Risk scoring & predatory detection (Phase 2+)
│   │   ├── rag/             # Retrieval-Augmented Generation & vector search (Phase 2+)
│   │   ├── llm/             # Modular LLM & embedding providers (OpenAI / Ollama / Qwen)
│   │   │   ├── base.py
│   │   │   ├── provider.py
│   │   │   └── embeddings.py
│   │   ├── utils/           # Utilities & structured logger
│   │   │   └── logger.py
│   │   └── main.py          # FastAPI application entrypoint
│   ├── tests/               # Pytest automated test suite
│   ├── alembic/             # Database migration scripts
│   ├── alembic.ini          # Alembic configuration
│   ├── Dockerfile           # Backend container build specification
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/      # React UI components (Health diagnostics, specs, roadmap)
│   │   ├── pages/           # Application views (Dashboard)
│   │   ├── services/        # API client routines
│   │   ├── hooks/           # Custom React hooks (useHealth telemetry)
│   │   ├── utils/           # App constants & helpers
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css        # Glassmorphic dark cyber theme
│   ├── index.html
│   ├── vite.config.js       # Vite configuration with backend reverse proxy
│   ├── package.json
│   └── Dockerfile           # Frontend container build specification
├── extension/               # Chrome Extension (Phase 4 placeholder)
├── data/                    # Privacy policy dataset storage
├── models/                  # Local GGUF/quantized weights storage
├── docker-compose.yml       # Multi-container orchestration (db, backend, frontend)
├── .env.example             # Environment configuration template
├── .gitignore               # Comprehensive Git exclusions
└── README.md                # Project documentation
```

---

## ⚙️ Environment Configuration

1. Copy `.env.example` to create `.env`:
   ```bash
   cp .env.example .env
   ```
2. Update the environment variables if necessary. All credentials and paths are parameterized without hardcoded secrets.

---

## 🚀 Running with Docker Compose (Recommended)

Ensure Docker Desktop (or Docker Engine with Docker Compose) is running on your machine:

1. **Start all services (Database, Backend, and Frontend):**
   ```bash
   docker compose up --build
   ```
   Or in detached background mode:
   ```bash
   docker compose up -d --build
   ```

2. **Access the services:**
   - **Frontend UI:** [http://localhost:3000](http://localhost:3000)
   - **Backend API:** [http://localhost:8000](http://localhost:8000)
   - **Interactive API Documentation (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Health Endpoint:** [http://localhost:8000/health](http://localhost:8000/health)
   - **PostgreSQL + pgvector:** `localhost:5432`

3. **Check container logs:**
   ```bash
   docker compose logs -f
   ```

4. **Stop the environment:**
   ```bash
   docker compose down
   ```

---

## 💻 Running Locally (Development Mode)

### 1. Database
Run PostgreSQL with the `pgvector` extension via Docker:
```bash
docker run -d --name fine_print_db -p 5432:5432 -e POSTGRES_DB=fine_print_auditor -e POSTGRES_USER=auditor_user -e POSTGRES_PASSWORD=auditor_password pgvector/pgvector:pg16
```

### 2. Backend (FastAPI)
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Run test suite:
```bash
pytest
```

### 3. Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🩺 Health Check API (`GET /health`)

The health endpoint provides instant operational verification of the FastAPI server, database connection, pgvector status, and modular AI subsystem.

### Request:
```http
GET /health HTTP/1.1
Host: localhost:8000
Accept: application/json
```

### Sample Response (`200 OK`):
```json
{
  "status": "healthy",
  "app_name": "AI-Powered Fine Print Auditor",
  "environment": "development",
  "version": "0.1.0",
  "timestamp": "2026-10-03T09:30:00.000000Z",
  "database": {
    "status": "connected",
    "pgvector_installed": true,
    "pgvector_version": "0.7.4",
    "error": null
  },
  "ai_subsystem": {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "embedding_provider": "openai"
  }
}
```

---

## 🧠 Modular AI Layer Architecture

The auditor is built for complete privacy-first independence:
- **Cloud Mode:** Set `AI_PROVIDER=openai` or `AI_PROVIDER=anthropic` in `.env` along with your API key.
- **Local / Offline Mode:** Set `AI_PROVIDER=ollama` and `OLLAMA_MODEL=qwen2.5:7b` to run entirely on local infrastructure with zero telemetry or data leakage.
- **Embeddings:** Seamlessly switch between OpenAI (`text-embedding-3-small`) and local sentence-transformers (`sentence-transformers/all-MiniLM-L6-v2`).

---

## 🗺️ Implementation Roadmap

| Phase | Milestone | Focus |
|---|---|---|
| **Phase 0** | **Foundation** *(Current)* | FastAPI, PostgreSQL + pgvector, React, Docker Compose, Health Telemetry |
| **Phase 1** | **Ingestion & Extraction** | Policy crawler, document clean-up, hierarchical chunking |
| **Phase 2** | **Risk Scoring & RAG** | Vector embeddings, pgvector similarity, unfair term classification |
| **Phase 3** | **Interactive Auditor** | Multi-turn conversational Q&A, clause comparison engine |
| **Phase 4** | **Chrome Extension** | Browser extension (Manifest V3) for automated in-browser policy auditing |
