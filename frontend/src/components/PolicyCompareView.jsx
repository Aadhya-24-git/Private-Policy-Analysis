import React, { useState } from 'react';
import {
  GitCompare,
  ArrowRight,
  PlusCircle,
  MinusCircle,
  FileDiff,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

export function PolicyCompareView({
  documents = [],
  onCompare,
  comparisonData = null,
  isComparing = false,
  error = null,
  initialOldDocId = '',
  initialNewDocId = '',
}) {
  const [oldDocId, setOldDocId] = useState(
    initialOldDocId || (documents.length > 1 ? documents[1].document_id : documents[0]?.document_id || '')
  );
  const [newDocId, setNewDocId] = useState(
    initialNewDocId || (documents.length > 0 ? documents[0].document_id : '')
  );
  const [activeFilter, setActiveFilter] = useState('all'); // 'all' | 'modified' | 'added' | 'removed'
  const [expandedClauses, setExpandedClauses] = useState({});

  React.useEffect(() => {
    if (initialOldDocId) setOldDocId(initialOldDocId);
  }, [initialOldDocId]);

  React.useEffect(() => {
    if (initialNewDocId) setNewDocId(initialNewDocId);
  }, [initialNewDocId]);

  const toggleExpand = (id) => {
    setExpandedClauses((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleRunComparison = (e) => {
    e.preventDefault();
    if (!oldDocId || !newDocId) return;
    onCompare(oldDocId, newDocId);
  };

  const summary = comparisonData?.summary;
  const modified = comparisonData?.modified_clauses || [];
  const added = comparisonData?.added_clauses || [];
  const removed = comparisonData?.removed_clauses || [];

  return (
    <div className="max-w-5xl mx-auto px-4 md:px-8 py-8 font-sans w-full">
      {/* Header */}
      <div className="mb-6">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-800 border border-emerald-200 mb-2">
          <GitCompare size={13} className="text-emerald-600" />
          <span>Semantic Policy Diff Engine</span>
        </div>
        <h2 className="text-xl md:text-2xl font-bold text-gray-900 tracking-tight">
          Compare Policy Versions
        </h2>
        <p className="text-xs text-gray-500 mt-1">
          Detect added, removed, and modified clauses between two legal agreements using semantic matching.
        </p>
      </div>

      {/* Document Selection Form */}
      <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm mb-6">
        <form onSubmit={handleRunComparison} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
            {/* Old Document Selector */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                Baseline Policy (Previous Version)
              </label>
              <select
                value={oldDocId}
                onChange={(e) => setOldDocId(e.target.value)}
                disabled={isComparing}
                className="w-full px-3 py-2 text-xs bg-gray-50/50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 text-gray-800"
                required
              >
                <option value="">Select baseline document...</option>
                {documents.map((doc) => (
                  <option key={doc.document_id} value={doc.document_id}>
                    {doc.filename || 'Untitled Policy'} ({doc.source_type?.toUpperCase()})
                  </option>
                ))}
              </select>
            </div>

            {/* New Document Selector */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                Updated Policy (New Version)
              </label>
              <select
                value={newDocId}
                onChange={(e) => setNewDocId(e.target.value)}
                disabled={isComparing}
                className="w-full px-3 py-2 text-xs bg-gray-50/50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 text-gray-800"
                required
              >
                <option value="">Select updated document...</option>
                {documents.map((doc) => (
                  <option key={doc.document_id} value={doc.document_id}>
                    {doc.filename || 'Untitled Policy'} ({doc.source_type?.toUpperCase()})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex justify-end pt-2 border-t border-gray-100">
            <button
              type="submit"
              disabled={isComparing || !oldDocId || !newDocId}
              className="inline-flex items-center gap-2 px-4 py-2 bg-gray-900 hover:bg-gray-800 text-white rounded-lg text-xs font-medium transition-all disabled:opacity-40"
            >
              {isComparing ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  <span>Matching clauses &amp; analyzing diffs...</span>
                </>
              ) : (
                <>
                  <GitCompare size={14} />
                  <span>Compare Policies</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 mb-6 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700 flex items-start gap-2.5">
          <AlertCircle size={16} className="mt-0.5 shrink-0 text-red-500" />
          <div>
            <span className="font-semibold">Comparison Error:</span> {error}
          </div>
        </div>
      )}

      {/* Comparison Results */}
      {comparisonData && (
        <div className="space-y-6">
          {/* Summary Banner */}
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-gray-100">
              <div className="flex items-center gap-2 text-xs font-semibold text-gray-900">
                <span className="text-gray-500 font-normal">Comparing:</span>
                <span className="px-2 py-0.5 rounded bg-gray-100 text-gray-800 font-mono">
                  {comparisonData.old_document_name}
                </span>
                <ArrowRight size={13} className="text-gray-400" />
                <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 font-mono border border-emerald-200">
                  {comparisonData.new_document_name}
                </span>
              </div>

              {/* Status Pills */}
              <div className="flex items-center gap-2 text-xs">
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200 font-medium">
                  <FileDiff size={12} />
                  {summary?.modified_count || 0} Modified
                </span>
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 font-medium">
                  <PlusCircle size={12} />
                  {summary?.added_count || 0} Added
                </span>
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-red-50 text-red-800 border border-red-200 font-medium">
                  <MinusCircle size={12} />
                  {summary?.removed_count || 0} Removed
                </span>
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200 font-medium">
                  <CheckCircle2 size={12} />
                  {summary?.unchanged_count || 0} Unchanged
                </span>
              </div>
            </div>

            <p className="text-xs text-gray-700 mt-3 leading-relaxed">
              {summary?.overview}
            </p>

            {/* Filter Tabs */}
            <div className="flex items-center gap-2 mt-4 pt-3 border-t border-gray-100 text-xs">
              <button
                type="button"
                onClick={() => setActiveFilter('all')}
                className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                  activeFilter === 'all'
                    ? 'bg-gray-900 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                All Changes ({modified.length + added.length + removed.length})
              </button>
              <button
                type="button"
                onClick={() => setActiveFilter('modified')}
                className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                  activeFilter === 'modified'
                    ? 'bg-amber-600 text-white'
                    : 'bg-amber-50 text-amber-800 border border-amber-200 hover:bg-amber-100'
                }`}
              >
                Modified ({modified.length})
              </button>
              <button
                type="button"
                onClick={() => setActiveFilter('added')}
                className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                  activeFilter === 'added'
                    ? 'bg-emerald-600 text-white'
                    : 'bg-emerald-50 text-emerald-800 border border-emerald-200 hover:bg-emerald-100'
                }`}
              >
                Added ({added.length})
              </button>
              <button
                type="button"
                onClick={() => setActiveFilter('removed')}
                className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                  activeFilter === 'removed'
                    ? 'bg-red-600 text-white'
                    : 'bg-red-50 text-red-800 border border-red-200 hover:bg-red-100'
                }`}
              >
                Removed ({removed.length})
              </button>
            </div>
          </div>

          {/* Section: Modified Clauses */}
          {(activeFilter === 'all' || activeFilter === 'modified') && modified.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                <FileDiff size={15} className="text-amber-600" />
                <span>Modified Clauses ({modified.length})</span>
              </h3>

              <div className="space-y-3">
                {modified.map((item, idx) => {
                  const isExpanded = !!expandedClauses[`mod-${idx}`];
                  return (
                    <div
                      key={idx}
                      className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm"
                    >
                      {/* Change Explanation */}
                      {item.explanation && (
                        <div className="mb-3 p-2.5 rounded-lg bg-amber-50/70 border border-amber-200/80 text-xs text-amber-900 flex items-start gap-2">
                          <span className="font-semibold shrink-0">Analysis:</span>
                          <span>{item.explanation}</span>
                        </div>
                      )}

                      {/* Side-by-Side Clause Comparison */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                        {/* Old Version */}
                        <div className="border border-red-100 bg-red-50/30 rounded-lg p-3">
                          <div className="flex items-center justify-between mb-1.5 text-[11px] text-red-800 font-medium">
                            <span className="flex items-center gap-1">
                              <MinusCircle size={12} />
                              Previous Policy (Clause #{item.old_clause.clause_order + 1})
                            </span>
                            <span className="text-[10px] text-gray-500">
                              {item.old_clause.section && `Sec: ${item.old_clause.section}`}
                              {item.old_clause.page_number && ` • P.${item.old_clause.page_number}`}
                            </span>
                          </div>
                          <blockquote
                            className={`font-mono text-[11.5px] text-gray-800 leading-relaxed ${
                              isExpanded ? '' : 'line-clamp-4'
                            }`}
                          >
                            &ldquo;{item.old_clause.clause_text}&rdquo;
                          </blockquote>
                        </div>

                        {/* New Version */}
                        <div className="border border-emerald-100 bg-emerald-50/30 rounded-lg p-3">
                          <div className="flex items-center justify-between mb-1.5 text-[11px] text-emerald-800 font-medium">
                            <span className="flex items-center gap-1">
                              <PlusCircle size={12} />
                              Updated Policy (Clause #{item.new_clause.clause_order + 1})
                            </span>
                            <span className="text-[10px] text-gray-500">
                              {item.new_clause.section && `Sec: ${item.new_clause.section}`}
                              {item.new_clause.page_number && ` • P.${item.new_clause.page_number}`}
                            </span>
                          </div>
                          <blockquote
                            className={`font-mono text-[11.5px] text-gray-800 leading-relaxed ${
                              isExpanded ? '' : 'line-clamp-4'
                            }`}
                          >
                            &ldquo;{item.new_clause.clause_text}&rdquo;
                          </blockquote>
                        </div>
                      </div>

                      <div className="mt-2 flex justify-between items-center text-[11px] text-gray-400">
                        <span>Similarity match: {Math.round((item.similarity_score || 0) * 100)}%</span>
                        <button
                          type="button"
                          onClick={() => toggleExpand(`mod-${idx}`)}
                          className="flex items-center gap-1 text-gray-500 hover:text-gray-800"
                        >
                          {isExpanded ? (
                            <>
                              <span>Collapse</span>
                              <ChevronUp size={12} />
                            </>
                          ) : (
                            <>
                              <span>Expand</span>
                              <ChevronDown size={12} />
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Section: Added Clauses */}
          {(activeFilter === 'all' || activeFilter === 'added') && added.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                <PlusCircle size={15} className="text-emerald-600" />
                <span>Newly Added Clauses ({added.length})</span>
              </h3>

              <div className="space-y-3">
                {added.map((item, idx) => (
                  <div
                    key={idx}
                    className="bg-white border border-emerald-200 rounded-xl p-4 shadow-sm"
                  >
                    <div className="flex items-center justify-between mb-2 text-xs">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 uppercase">
                          Added in New Version
                        </span>
                        {item.new_clause.section && (
                          <span className="text-gray-600 font-medium">
                            Section: &ldquo;{item.new_clause.section}&rdquo;
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-gray-400">
                        {item.new_clause.page_number && <span>Page {item.new_clause.page_number} • </span>}
                        <span>Clause #{item.new_clause.clause_order + 1}</span>
                      </div>
                    </div>

                    <blockquote className="font-mono text-xs text-gray-800 bg-emerald-50/30 border-l-2 border-emerald-500 p-3 rounded-r-lg leading-relaxed">
                      &ldquo;{item.new_clause.clause_text}&rdquo;
                    </blockquote>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Section: Removed Clauses */}
          {(activeFilter === 'all' || activeFilter === 'removed') && removed.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                <MinusCircle size={15} className="text-red-600" />
                <span>Removed Clauses ({removed.length})</span>
              </h3>

              <div className="space-y-3">
                {removed.map((item, idx) => (
                  <div
                    key={idx}
                    className="bg-white border border-red-200 rounded-xl p-4 shadow-sm"
                  >
                    <div className="flex items-center justify-between mb-2 text-xs">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-800 uppercase">
                          Excised from New Version
                        </span>
                        {item.old_clause.section && (
                          <span className="text-gray-600 font-medium">
                            Section: &ldquo;{item.old_clause.section}&rdquo;
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-gray-400">
                        {item.old_clause.page_number && <span>Page {item.old_clause.page_number} • </span>}
                        <span>Clause #{item.old_clause.clause_order + 1}</span>
                      </div>
                    </div>

                    <blockquote className="font-mono text-xs text-gray-800 bg-red-50/30 border-l-2 border-red-500 p-3 rounded-r-lg leading-relaxed">
                      &ldquo;{item.old_clause.clause_text}&rdquo;
                    </blockquote>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Clean State: Zero Changes */}
          {modified.length === 0 && added.length === 0 && removed.length === 0 && (
            <div className="bg-white border border-gray-200 rounded-2xl p-8 text-center">
              <CheckCircle2 size={36} className="text-emerald-500 mx-auto mb-2" />
              <h4 className="text-sm font-semibold text-gray-900">Policies Are Identical</h4>
              <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
                No additions, removals, or meaningful wording modifications were detected between these versions.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
