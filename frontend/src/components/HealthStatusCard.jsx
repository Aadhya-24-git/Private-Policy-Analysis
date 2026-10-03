import React, { useState } from 'react';
import { 
  Server, 
  Database, 
  Cpu, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  Code,
  Layers
} from 'lucide-react';

export function HealthStatusCard({ 
  healthData, 
  loading, 
  error, 
  latencyMs, 
  lastChecked, 
  onRefresh 
}) {
  const [showJson, setShowJson] = useState(false);

  const isFastApiRunning = !error && healthData?.status === 'healthy';
  const isDbConnected = healthData?.database?.status === 'connected';
  const hasPgVector = Boolean(healthData?.database?.pgvector_installed);

  return (
    <div className="card-glass">
      <div className="status-header">
        <div className="status-title-group">
          <div className="status-icon-wrap">
            <Server size={20} color="#10b981" />
          </div>
          <div>
            <h3>System Telemetry & Health Diagnostics</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Real-time polling from endpoint: <code style={{ color: 'var(--accent-cyan)' }}>GET /health</code>
            </p>
          </div>
        </div>

        <button 
          className="ping-button" 
          onClick={onRefresh} 
          disabled={loading}
          title="Query GET /health diagnostic endpoint"
        >
          <RefreshCw size={15} className={loading ? 'spin-icon' : ''} />
          <span>{loading ? 'Checking...' : 'Run Diagnostics'}</span>
        </button>
      </div>

      <div className="status-rows">
        {/* FastAPI Application Status */}
        <div className="status-row">
          <div className="row-label">
            <Server size={18} color="var(--accent-cyan)" />
            <div>
              <div>FastAPI Application Server</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                {healthData ? `${healthData.app_name} (v${healthData.version})` : 'Awaiting heartbeat...'}
              </div>
            </div>
          </div>
          <div className={`badge-status ${isFastApiRunning ? 'healthy' : 'error'}`}>
            {isFastApiRunning ? <CheckCircle2 size={13} /> : <AlertCircle size={13} />}
            <span>{isFastApiRunning ? 'RUNNING (200 OK)' : (error ? 'OFFLINE' : 'INITIALIZING')}</span>
          </div>
        </div>

        {/* PostgreSQL Database Status */}
        <div className="status-row">
          <div className="row-label">
            <Database size={18} color="var(--accent-emerald)" />
            <div>
              <div>PostgreSQL 16 Engine</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Driver: psycopg (SQLAlchemy 2.0 ORM)
              </div>
            </div>
          </div>
          <div className={`badge-status ${isDbConnected ? 'connected' : 'error'}`}>
            {isDbConnected ? <CheckCircle2 size={13} /> : <AlertCircle size={13} />}
            <span>{isDbConnected ? 'CONNECTED' : (healthData?.database?.error ? 'DISCONNECTED' : 'STANDBY')}</span>
          </div>
        </div>

        {/* pgvector Extension Status */}
        <div className="status-row">
          <div className="row-label">
            <Layers size={18} color="var(--accent-purple)" />
            <div>
              <div>pgvector Extension</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Vector similarity search & high-dimensional embeddings
              </div>
            </div>
          </div>
          <div className={`badge-status ${hasPgVector ? 'connected' : 'info'}`}>
            {hasPgVector ? <CheckCircle2 size={13} /> : <Clock size={13} />}
            <span>
              {hasPgVector 
                ? `ACTIVE (v${healthData?.database?.pgvector_version || '0.7'})` 
                : (isDbConnected ? 'NOT INSTALLED' : 'DOCKER PGVECTOR TARGET')}
            </span>
          </div>
        </div>

        {/* Modular AI Layer Status */}
        <div className="status-row">
          <div className="row-label">
            <Cpu size={18} color="var(--accent-cyan)" />
            <div>
              <div>Modular AI Subsystem</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Provider: <strong>{healthData?.ai_subsystem?.provider || 'Modular Engine'}</strong> | Model: {healthData?.ai_subsystem?.model || 'gpt-4o-mini / qwen2.5'}
              </div>
            </div>
          </div>
          <div className="badge-status info">
            <CheckCircle2 size={13} />
            <span>MODULAR READY</span>
          </div>
        </div>
      </div>

      {/* Latency and timestamp footer */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between', 
        marginTop: '18px', 
        paddingTop: '14px', 
        borderTop: '1px solid var(--border-subtle)',
        fontSize: '0.78rem',
        color: 'var(--text-secondary)'
      }}>
        <div style={{ display: 'flex', gap: '16px' }}>
          <span>Latency: <strong style={{ color: 'var(--accent-emerald)' }}>{latencyMs !== null ? `${latencyMs}ms` : '—'}</strong></span>
          <span>Last Checked: {lastChecked ? lastChecked.toLocaleTimeString() : 'Never'}</span>
        </div>

        <button 
          onClick={() => setShowJson(!showJson)}
          style={{ 
            background: 'transparent', 
            border: 'none', 
            color: 'var(--accent-cyan)', 
            cursor: 'pointer',
            fontSize: '0.78rem',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px'
          }}
        >
          <Code size={13} />
          <span>{showJson ? 'Hide Raw JSON' : 'Inspect /health JSON'}</span>
        </button>
      </div>

      {showJson && (
        <pre className="code-preview">
          {JSON.stringify(healthData || { error }, null, 2)}
        </pre>
      )}
    </div>
  );
}
