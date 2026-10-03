import React from 'react';
import { X, CheckCircle2, AlertCircle, RefreshCw, Cpu, Database, Server } from 'lucide-react';
import { API_BASE_URL } from '../utils/constants';

export function SettingsModal({
  isOpen,
  onClose,
  healthData,
  latencyMs,
  isLoading,
  error,
  onRefresh,
}) {
  if (!isOpen) return null;

  const isHealthy = !error && healthData?.status === 'healthy';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs font-sans">
      <div
        className="w-full max-w-md bg-white border border-gray-200 rounded-2xl shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-gray-900">System Configuration &amp; Health</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4 text-xs">
          {/* Status Banner */}
          <div
            className={`p-3 rounded-xl border flex items-center justify-between ${
              isHealthy
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : 'bg-red-50 border-red-200 text-red-800'
            }`}
          >
            <div className="flex items-center gap-2">
              {isHealthy ? (
                <CheckCircle2 size={16} className="text-emerald-600 shrink-0" />
              ) : (
                <AlertCircle size={16} className="text-red-600 shrink-0" />
              )}
              <div>
                <p className="font-semibold">{isHealthy ? 'FastAPI Backend Operational' : 'Backend Connection Issue'}</p>
                <p className="text-[11px] opacity-80">
                  {isHealthy ? `Latency: ${latencyMs}ms` : error || 'Unable to connect to server'}
                </p>
              </div>
            </div>

            <button
              onClick={onRefresh}
              disabled={isLoading}
              className="p-1.5 rounded-lg bg-white/80 hover:bg-white text-gray-700 shadow-xs border border-gray-200 transition-all disabled:opacity-50"
              title="Refresh status"
            >
              <RefreshCw size={13} className={isLoading ? 'animate-spin' : ''} />
            </button>
          </div>

          {/* Diagnostics Details */}
          <div className="space-y-2.5">
            <div className="flex items-center justify-between py-1.5 border-b border-gray-100">
              <span className="text-gray-500 flex items-center gap-1.5">
                <Database size={13} className="text-gray-400" />
                PostgreSQL &amp; pgvector
              </span>
              <span className="font-mono font-medium text-gray-800">
                {healthData?.database?.pgvector_installed
                  ? `Installed (v${healthData.database.pgvector_version || '0.7+'})`
                  : 'Pending'}
              </span>
            </div>

            <div className="flex items-center justify-between py-1.5 border-b border-gray-100">
              <span className="text-gray-500 flex items-center gap-1.5">
                <Cpu size={13} className="text-gray-400" />
                Configured AI Provider
              </span>
              <span className="font-mono font-medium text-gray-800 uppercase">
                {healthData?.ai_subsystem?.provider || 'openai'}
              </span>
            </div>

            <div className="flex items-center justify-between py-1.5 border-b border-gray-100">
              <span className="text-gray-500 flex items-center gap-1.5">
                <Cpu size={13} className="text-gray-400" />
                Active Model
              </span>
              <span className="font-mono font-medium text-gray-800">
                {healthData?.ai_subsystem?.model || 'gpt-4o-mini'}
              </span>
            </div>

            <div className="flex items-center justify-between py-1.5 border-b border-gray-100">
              <span className="text-gray-500 flex items-center gap-1.5">
                <Server size={13} className="text-gray-400" />
                API Target
              </span>
              <span className="font-mono font-medium text-gray-600 truncate max-w-[180px]">
                {API_BASE_URL || '/ (Local Proxy)'}
              </span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 bg-gray-50 border-t border-gray-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-3.5 py-1.5 text-xs font-medium text-gray-700 bg-white hover:bg-gray-100 border border-gray-200 rounded-lg transition-colors shadow-xs"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
