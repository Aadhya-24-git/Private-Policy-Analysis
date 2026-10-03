import React from 'react';
import { HealthStatusCard } from '../components/HealthStatusCard';
import { SystemArchitecture } from '../components/SystemArchitecture';
import { RoadmapTimeline } from '../components/RoadmapTimeline';
import { useHealth } from '../hooks/useHealth';
import { Sparkles, ShieldCheck } from 'lucide-react';

export function Dashboard() {
  const {
    healthData,
    loading,
    error,
    latencyMs,
    lastChecked,
    refresh,
  } = useHealth();

  return (
    <div className="dashboard-content" style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Hero section */}
      <section className="hero-section">
        <div className="hero-tag">
          <Sparkles size={14} />
          <span>System Foundation Active</span>
        </div>
        <h2 className="hero-title">
          Unmask deceptive clauses with <span className="gradient-text">autonomous intelligence</span>.
        </h2>
        <p className="hero-subtitle">
          Phase 0 establishes the containerized foundation: FastAPI core engine, PostgreSQL 16 with pgvector extension, React Vite interface, and modular LLM abstraction layer.
        </p>
      </section>

      {/* Primary Grid: Health Monitor & System Specs */}
      <div className="grid-2">
        <HealthStatusCard
          healthData={healthData}
          loading={loading}
          error={error}
          latencyMs={latencyMs}
          lastChecked={lastChecked}
          onRefresh={refresh}
        />
        <SystemArchitecture />
      </div>

      {/* Roadmap Timeline */}
      <RoadmapTimeline />
    </div>
  );
}
