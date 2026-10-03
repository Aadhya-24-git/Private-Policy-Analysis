import React from 'react';
import { Layers, Terminal, Box } from 'lucide-react';
import { SYSTEM_STACK } from '../utils/constants';

export function SystemArchitecture() {
  return (
    <div className="card-glass">
      <div className="status-header">
        <div className="status-title-group">
          <div className="status-icon-wrap">
            <Box size={20} color="var(--accent-cyan)" />
          </div>
          <div>
            <h3>Technology Foundation Specifications</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Engineered with Python FastAPI, PostgreSQL + pgvector, React + Vite & Docker
            </p>
          </div>
        </div>
      </div>

      <div className="tech-pill-grid">
        {SYSTEM_STACK.map((item, idx) => (
          <div className="tech-card" key={idx}>
            <span className="tech-role">{item.role}</span>
            <span className="tech-name">{item.name}</span>
            <span className="tech-version">{item.version}</span>
          </div>
        ))}
      </div>

      <div style={{ marginTop: '20px', padding: '14px', background: 'rgba(255, 255, 255, 0.02)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-purple)' }}>
          <Terminal size={15} />
          <span>Docker Compose Multi-Container Orchestration</span>
        </div>
        <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '6px' }}>
          Configured services: <code>fine_print_db</code> (pgvector/pgvector:pg16), <code>fine_print_backend</code> (FastAPI / Uvicorn), and <code>fine_print_frontend</code> (React Vite) connected across isolated network <code>fine_print_network</code>.
        </p>
      </div>
    </div>
  );
}
