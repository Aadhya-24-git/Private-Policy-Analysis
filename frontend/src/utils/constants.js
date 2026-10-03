export const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const SYSTEM_STACK = [
  { role: 'Frontend', name: 'React 18', version: 'Vite 5' },
  { role: 'Backend API', name: 'FastAPI', version: '0.115' },
  { role: 'Language', name: 'Python', version: '3.13' },
  { role: 'Database', name: 'PostgreSQL', version: '16' },
  { role: 'Vector Store', name: 'pgvector', version: '0.7+' },
  { role: 'ORM Engine', name: 'SQLAlchemy', version: '2.0' },
  { role: 'DB Driver', name: 'psycopg', version: '3.2' },
  { role: 'Migrations', name: 'Alembic', version: '1.13' },
  { role: 'Containers', name: 'Docker Compose', version: 'v2' },
];

export const ROADMAP_PHASES = [
  {
    phase: 'Phase 0',
    title: 'Foundation',
    desc: 'FastAPI, PostgreSQL + pgvector, React, Docker Compose foundation & health telemetry.',
    active: true,
  },
  {
    phase: 'Phase 1',
    title: 'Extraction',
    desc: 'Automated legal document ingestion, chunking, and metadata parsing pipeline.',
    active: false,
  },
  {
    phase: 'Phase 2',
    title: 'Risk Scoring & RAG',
    desc: 'pgvector semantic search, predatory clause flagging, and modular LLM auditor.',
    active: false,
  },
  {
    phase: 'Phase 3',
    title: 'Auditor Assistant',
    desc: 'Interactive chat assistant, clause comparison, and plain-language summaries.',
    active: false,
  },
  {
    phase: 'Phase 4',
    title: 'Extension & Polish',
    desc: 'Chrome extension (Manifest V3) for one-click real-time webpage auditing.',
    active: false,
  },
];
