import React from 'react';
import { ShieldAlert, Activity, Cpu } from 'lucide-react';

export function Header({ isHealthy }) {
  return (
    <header className="header-glass">
      <div className="brand-wrapper">
        <div className="logo-badge">
          <ShieldAlert size={26} />
        </div>
        <div className="brand-info">
          <h1>AI-Powered Fine Print Auditor</h1>
          <p>Autonomous Legal Analysis, Predatory Clause Detection & Privacy Intelligence</p>
        </div>
      </div>

      <div className="header-actions">
        <div className="phase-pill">
          <div className="pulse-dot" style={{ backgroundColor: isHealthy ? '#10b981' : '#f43f5e' }} />
          <span>PHASE 0: FOUNDATION</span>
        </div>
      </div>
    </header>
  );
}
