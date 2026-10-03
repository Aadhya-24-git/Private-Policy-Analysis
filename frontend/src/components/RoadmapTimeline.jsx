import React from 'react';
import { Milestone, ArrowRight } from 'lucide-react';
import { ROADMAP_PHASES } from '../utils/constants';

export function RoadmapTimeline() {
  return (
    <div className="card-glass timeline-card">
      <div className="status-header">
        <div className="status-title-group">
          <div className="status-icon-wrap">
            <Milestone size={20} color="var(--accent-purple)" />
          </div>
          <div>
            <h3>Project Implementation Blueprint</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Phased development lifecycle of the AI-Powered Fine Print Auditor
            </p>
          </div>
        </div>
      </div>

      <div className="timeline-steps">
        {ROADMAP_PHASES.map((item, idx) => (
          <div className={`step-card ${item.active ? 'active' : ''}`} key={idx}>
            <div className="step-phase">{item.phase}</div>
            <div className="step-title">{item.title}</div>
            <div className="step-desc">{item.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
