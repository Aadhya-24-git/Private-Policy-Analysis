import React from 'react';
import { FileText, ShieldAlert, Sparkles, RefreshCw, Layers } from 'lucide-react';

export function DocumentHeader({
  document,
  findingsCount = 0,
  activeTab = 'chat',
  onTabChange,
  onRunAudit,
  isAuditing = false,
}) {
  if (!document) return null;

  return (
    <header className="sticky top-0 z-10 bg-white/95 backdrop-blur-sm border-b border-gray-200 px-6 py-3.5 flex flex-wrap items-center justify-between gap-4 font-sans">
      <div className="flex items-center gap-3 min-w-0">
        <div className="w-9 h-9 rounded-lg bg-gray-100 border border-gray-200 flex items-center justify-center text-gray-600 shrink-0">
          <FileText size={18} />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h2 className="text-sm md:text-base font-semibold text-gray-900 truncate">
              {document.filename || 'Untitled Policy Document'}
            </h2>
            <span className="uppercase text-[10px] font-bold px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 border border-gray-200 shrink-0">
              {document.source_type}
            </span>
          </div>
          <div className="flex items-center gap-3 text-xs text-gray-500 mt-0.5">
            {document.total_clauses !== undefined && (
              <span className="flex items-center gap-1">
                <Layers size={13} className="text-gray-400" />
                {document.total_clauses} clauses extracted
              </span>
            )}
            <span>&bull;</span>
            <span className="capitalize text-emerald-600 font-medium">
              {document.status || 'indexed'}
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {/* View Toggle Tabs */}
        <div className="flex bg-gray-100 p-0.5 rounded-lg border border-gray-200 text-xs">
          <button
            onClick={() => onTabChange('chat')}
            className={`px-3 py-1.5 rounded-md font-medium transition-all ${
              activeTab === 'chat'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Auditor Chat
          </button>
          <button
            onClick={() => onTabChange('findings')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-all ${
              activeTab === 'findings'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <span>Risk Findings</span>
            {findingsCount > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-red-100 text-red-700">
                {findingsCount}
              </span>
            )}
          </button>
        </div>

        {/* Audit Button */}
        <button
          onClick={onRunAudit}
          disabled={isAuditing}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-lg transition-colors disabled:opacity-50"
          title="Run the 7-category risk rule engine"
        >
          <Sparkles size={14} className={isAuditing ? 'animate-spin' : ''} />
          <span>{isAuditing ? 'Auditing...' : 'Run Audit'}</span>
        </button>
      </div>
    </header>
  );
}
