# AI-Powered Fine Print Auditor

> Autonomous legal intelligence engine designed to analyze complex Terms of Service, Privacy Policies, and EULAs to surface hidden privacy risks, potentially unfair clauses, and important legal terms.

---

## 📌 Project Overview

The AI-Powered Fine Print Auditor is an intelligent document analysis system that helps users understand complex privacy policies and legal documents.

The system analyzes uploaded policy documents, identifies potentially risky clauses, provides evidence from the original document, answers policy-related questions using document-grounded AI, and compares different versions of policies.

The project combines rule-based risk detection, Retrieval-Augmented Generation (RAG), vector similarity search, local Qwen3 AI, and PostgreSQL with pgvector.

---

## ✨ Key Features

- **📄 Document Upload & Extraction** — Supports PDF, DOCX, TXT, and pasted policy text.
- **⚠️ Risk Detection** — Detects Auto-Renewal, Hidden Fees, Arbitration, Data Sharing, Cancellation, Data Retention, and Liability clauses.
- **🔎 Evidence-Based Findings** — Every detected finding is linked to the original policy clause and its source information.
- **🤖 Policy Q&A** — Ask questions about an uploaded policy and receive answers grounded in the document.
- **🧠 RAG & Vector Search** — Retrieves relevant policy clauses using semantic similarity search.
- **💬 Chat History** — Maintains questions and answers associated with analyzed policies.
- **📊 Policy Comparison** — Compares two policy versions and identifies added, removed, modified, and unchanged clauses.
- **🔐 Security Hardening** — Includes file validation, path traversal protection, upload limits, prompt injection isolation, credential redaction, safe error handling, and security headers.
- **🐳 Docker Deployment** — Runs the frontend, backend, and PostgreSQL database using Docker Compose.
- **🧪 Automated Testing** — Includes comprehensive backend tests and frontend build validation.
- **💻 Local AI Processing** — Uses Ollama with Qwen3:4b for local policy analysis and Qwen3 Embedding 0.6B for embeddings.

---

## 🛠️ Technology Stack

### Backend

- Python 3.13
- FastAPI
- Uvicorn
- SQLAlchemy 2.0
- Pydantic

### Database

- PostgreSQL 16
- pgvector
- psycopg 3

### Database Migrations

- Alembic

### Frontend

- React
- Vite
- Modern Vanilla CSS

### AI / RAG

- Ollama
- Qwen3:4b
- Qwen3 Embedding 0.6B
- Retrieval-Augmented Generation
- Vector Similarity Search

### Document Processing

- PyMuPDF
- python-docx

### Deployment

- Docker
- Docker Compose

### Testing

- Pytest
- Frontend production build validation

---

## 📁 Project Directory Structure

```text
fine-print-auditor/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── endpoints/
│   │   │           ├── analyze.py
│   │   │           ├── chat.py
│   │   │           ├── compare.py
│   │   │           ├── documents.py
│   │   │           └── health.py
│   │   ├── analysis/
│   │   │   └── rules/
│   │   │       ├── auto_renewal.py
│   │   │       ├── hidden_fees.py
│   │   │       ├── arbitration.py
│   │   │       ├── data_sharing.py
│   │   │       ├── cancellation.py
│   │   │       ├── data_retention.py
│   │   │       └── liability.py
│   │   ├── comparison/
│   │   │   ├── matcher.py
│   │   │   ├── explainer.py
│   │   │   └── service.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── database/
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   ├── extraction/
│   │   ├── llm/
│   │   │   ├── base.py
│   │   │   ├── provider.py
│   │   │   └── embeddings.py
│   │   ├── models/
│   │   ├── rag/
│   │   │   ├── retriever.py
│   │   │   ├── context.py
│   │   │   └── qa_service.py
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── utils/
│   │   └── main.py
│   ├── tests/
│   ├── alembic/
│   ├── scripts/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.jsx
│   │   │   ├── DocumentHeader.jsx
│   │   │   ├── UploadView.jsx
│   │   │   ├── FindingsList.jsx
│   │   │   ├── RiskBadge.jsx
│   │   │   ├── ChatStream.jsx
│   │   │   ├── ChatComposer.jsx
│   │   │   ├── PolicyCompareView.jsx
│   │   │   └── SettingsModal.jsx
│   │   ├── services/
│   │   ├── App.jsx
│   │   └── index.css
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── Dockerfile
│
├── data/
├── models/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
⚙️ Environment Configuration
The current system uses Ollama for local AI processing.
AI_PROVIDER=ollama
AI_MODEL=qwen3:4b

EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=qwen3-embedding:0.6b
EMBEDDING_DIMENSION=1024

OLLAMA_TIMEOUT=180

The backend communicates with Ollama running on the host machine through:
http://host.docker.internal:11434

🚀 Running with Docker Compose
Ensure Docker Desktop is running.
1. Start all services
docker compose up --build

Or run in detached mode:
docker compose up -d --build

The application starts:
- PostgreSQL + pgvector
- FastAPI backend
- React frontend
Database migrations are automatically applied during backend startup.
2. Access the services
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- PostgreSQL: localhost:5432
3. Check container status
docker compose ps

4. View logs
docker compose logs -f

For backend logs:
docker compose logs -f backend

5. Stop the application
docker compose down

💻 Running Locally
Backend
cd backend
python -m venv .venv

Windows:
.venv\Scripts\activate

Linux/macOS:
source .venv/bin/activate

Install dependencies:
pip install -r requirements.txt

Run the backend:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

Frontend
cd frontend
npm install
npm run dev

Open:
http://localhost:3000

Run Tests
cd backend
pytest

🔌 API Endpoints
Document Analysis
POST /api/v1/analyze/file
POST /api/v1/analyze/text

Uploads and analyzes policy documents or supplied text.
Policy Audit
GET /api/v1/documents/{document_id}/audit
GET /api/v1/documents/{document_id}/findings

Retrieves detected risks and findings.
Policy Q&A
POST /api/v1/documents/{document_id}/ask
POST /api/v1/documents/{document_id}/chat
POST /api/v1/chat/ask

Provides document-grounded policy questions and answers.
Policy Comparison
POST /api/v1/compare

Compares two policy documents or policy versions.
Health Check
GET /health

Checks backend and database availability.
🧠 RAG & AI Architecture
                 Policy Document
                       │
                       ▼
              Document Extraction
                       │
                       ▼
                 Clause Splitting
                       │
                       ▼
              Qwen3 Embedding 0.6B
                       │
                       ▼
              PostgreSQL + pgvector
                       │
                       ▼
               Semantic Retrieval
                       │
                       ▼
                Relevant Clauses
                       │
                       ▼
                  Qwen3:4b
                    Ollama
                       │
                       ▼
               Grounded Response

The RAG system retrieves relevant clauses from the analyzed policy before generating an answer.
The AI is instructed to answer only using the supplied policy content. If the requested information is not present in the available clauses, the system returns:
Based on the provided policy clauses, this information is not specified in the document.

This reduces unsupported or hallucinated answers.
⚠️ Risk Detection Engine
The rule-based analysis engine currently detects seven categories:
Category	Description
Auto-Renewal	Detects automatic subscription or contract renewal
Hidden Fees	Identifies additional or unexpected charges
Arbitration	Detects mandatory arbitration clauses
Data Sharing	Identifies sharing of user information
Cancellation	Detects cancellation conditions and restrictions
Data Retention	Identifies data retention practices
Liability	Detects liability limitations


Every finding maintains a connection to its original policy clause.
📊 Policy Comparison
The policy comparison engine compares two versions of a policy and identifies:
- Added clauses
- Removed clauses
- Modified clauses
- Unchanged clauses
The matching process uses:
- Normalized text comparison
- Semantic similarity
- Lexical similarity
- Clause matching
- Deterministic token-level differences
- Grounded AI explanations
The frontend also prevents stale comparison results from being displayed when the selected documents are changed.
🔐 Security
The application includes security protections for both uploaded documents and AI processing.
Implemented protections include:
- Filename sanitization
- Path traversal protection
- File type validation
- File size limits
- Chunked upload protection
- DOCX Zip Slip protection
- CORS restrictions
- Security headers
- Prompt injection isolation
- Credential redaction
- Safe error handling
- Database transaction rollback handling
- Safe frontend rendering
🧪 Testing & Validation
The project includes automated tests for:
- Document extraction
- Rule-based risk detection
- RAG retrieval
- Embedding generation
- AI provider behavior
- Policy Q&A
- Policy comparison
- Security validation
- API endpoints
- Docker integration
- Regression cases
Latest verified backend test result:
127 passed
6 skipped

Frontend production build was also successfully validated using:
npm run build

📊 Current Implementation Status
Component	Status
Document Upload & Extraction	✅ Complete
PDF / DOCX / TXT Support	✅ Complete
Rule-Based Risk Detection	✅ Complete
RAG & Vector Search	✅ Complete
Qwen3:4b Local AI	✅ Complete
Qwen3 Embeddings	✅ Complete
Policy Q&A	✅ Complete
Chat History	✅ Complete
Policy Comparison	✅ Complete
Security Hardening	✅ Complete
Docker Deployment	✅ Complete
Automated Testing	✅ Complete


🎯 Project Objective
The objective of the AI-Powered Fine Print Auditor is to make complex legal and privacy documents easier to understand by identifying potentially risky clauses, explaining their meaning in simple language, and providing evidence directly from the original document.
The system focuses on:
Transparency → Evidence → Explainability → Privacy → Document-Grounded AI