import React from 'react';
import { Plus, FileText, Settings, ShieldCheck, AlertCircle, Clock, Trash2, GitCompare } from 'lucide-react';

export function Sidebar({
  documents = [],
  selectedDocId = null,
  onSelectDoc,
  onNewPolicy,
  onOpenSettings,
  onOpenCompare,
  viewMode = 'policy',
  backendConnected = true,
  isOpen = true,
  onClose,
}) {
  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 z-20 md:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed md:static inset-y-0 left-0 z-30 w-64 bg-[#f9fafb] border-r border-gray-200 flex flex-col justify-between transition-transform duration-200 ease-in-out font-sans ${
          isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        {/* Top Header & Navigation Actions */}
        <div className="p-3 border-b border-gray-200">
          <div className="flex items-center gap-2 px-2 py-1.5 mb-2">
            <div className="w-7 h-7 rounded-lg bg-emerald-600 text-white flex items-center justify-center font-bold text-sm shadow-sm">
              §
            </div>
            <div className="leading-tight">
              <h1 className="text-sm font-semibold text-gray-900 tracking-tight">Fine Print Auditor</h1>
              <span className="text-[11px] text-gray-500">Legal Risk Intelligence</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-1.5">
            <button
              onClick={onNewPolicy}
              className={`flex items-center justify-center gap-1.5 px-2.5 py-2 text-xs font-medium rounded-lg border transition-all ${
                viewMode === 'policy' && !selectedDocId
                  ? 'bg-emerald-50 border-emerald-300 text-emerald-800 shadow-sm font-semibold'
                  : 'bg-white hover:bg-gray-50 active:bg-gray-100 border-gray-200 text-gray-800 shadow-sm'
              }`}
              title="Upload new policy"
            >
              <Plus size={14} className={viewMode === 'policy' && !selectedDocId ? 'text-emerald-700' : 'text-gray-600'} />
              <span>New Policy</span>
            </button>

            <button
              onClick={onOpenCompare}
              className={`flex items-center justify-center gap-1.5 px-2.5 py-2 text-xs font-medium rounded-lg border transition-all ${
                viewMode === 'compare'
                  ? 'bg-emerald-50 border-emerald-300 text-emerald-800 shadow-sm font-semibold'
                  : 'bg-white hover:bg-gray-50 active:bg-gray-100 border-gray-200 text-gray-800 shadow-sm'
              }`}
              title="Compare two policy versions"
            >
              <GitCompare size={14} className={viewMode === 'compare' ? 'text-emerald-700' : 'text-gray-600'} />
              <span>Compare</span>
            </button>
          </div>
        </div>

        {/* Recent Policies List */}
        <div className="flex-1 overflow-y-auto px-2 py-3 space-y-1">
          <div className="px-3 pb-1 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
            Previous Policies
          </div>

          {documents.length === 0 ? (
            <div className="px-3 py-6 text-center text-xs text-gray-400">
              <Clock size={16} className="mx-auto mb-1.5 opacity-60" />
              <span>No policies uploaded yet</span>
            </div>
          ) : (
            documents.map((doc) => {
              const isSelected = selectedDocId === doc.document_id;
              const formattedDate = doc.upload_time
                ? new Date(doc.upload_time).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                  })
                : '';

              return (
                <button
                  key={doc.document_id}
                  onClick={() => onSelectDoc(doc.document_id)}
                  className={`w-full text-left flex items-start gap-2.5 px-3 py-2 rounded-lg text-xs transition-colors group ${
                    isSelected
                      ? 'bg-gray-200/80 text-gray-900 font-medium'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  <FileText
                    size={15}
                    className={`mt-0.5 shrink-0 ${
                      isSelected ? 'text-emerald-700' : 'text-gray-400 group-hover:text-gray-600'
                    }`}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="truncate leading-snug">
                      {doc.filename || 'Direct Text Policy'}
                    </p>
                    <div className="flex items-center gap-2 mt-0.5 text-[10px] text-gray-400">
                      <span className="uppercase">{doc.source_type}</span>
                      {formattedDate && <span>&bull; {formattedDate}</span>}
                    </div>
                  </div>
                </button>
              );
            })
          )}
        </div>

        {/* Sidebar Footer: Settings & Connection Status */}
        <div className="p-3 border-t border-gray-200 bg-[#f9fafb]">
          <button
            onClick={onOpenSettings}
            className="w-full flex items-center justify-between px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <div className="flex items-center gap-2">
              <Settings size={15} className="text-gray-500" />
              <span>Settings & Status</span>
            </div>
            <span
              className={`w-2 h-2 rounded-full ${
                backendConnected ? 'bg-emerald-500 ring-2 ring-emerald-100' : 'bg-red-500 ring-2 ring-red-100'
              }`}
              title={backendConnected ? 'Backend Connected' : 'Backend Offline'}
            />
          </button>
        </div>
      </aside>
    </>
  );
}
