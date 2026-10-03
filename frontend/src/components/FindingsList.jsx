import React, { useState } from 'react';
import { RiskBadge, CategoryBadge } from './RiskBadge';
import { ShieldCheck, MessageSquare, ChevronDown, ChevronUp, Copy, Check } from 'lucide-react';

export function FindingsList({
  findings = [],
  summary = null,
  onAskClause,
  isLoading = false,
}) {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedRisk, setSelectedRisk] = useState('all');
  const [expandedClauses, setExpandedClauses] = useState({});
  const [copiedId, setCopiedId] = useState(null);

  const toggleClauseExpand = (id) => {
    setExpandedClauses((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const handleCopyText = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Filter findings
  const filteredFindings = findings.filter((f) => {
    if (selectedCategory !== 'all' && f.category !== selectedCategory) return false;
    if (selectedRisk !== 'all' && f.risk_level?.toLowerCase() !== selectedRisk) return false;
    return true;
  });

  const categories = [
    { key: 'all', label: 'All Categories' },
    { key: 'auto_renewal', label: 'Auto-renewal' },
    { key: 'hidden_fees', label: 'Hidden Fees' },
    { key: 'arbitration', label: 'Arbitration' },
    { key: 'data_sharing', label: 'Data Sharing' },
    { key: 'cancellation', label: 'Cancellation' },
    { key: 'data_retention', label: 'Data Retention' },
    { key: 'liability', label: 'Liability' },
  ];

  return (
    <div className="max-w-4xl mx-auto px-6 py-6 font-sans">
      {/* Risk Summary Metrics Bar */}
      <div className="bg-white border border-gray-200 rounded-xl p-4 mb-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-semibold text-gray-900">Automated Risk Tagging Profile</h3>
            <p className="text-xs text-gray-500 mt-0.5">
              Deterministic rule engine evaluation across 7 fine-print categories
            </p>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700 font-medium">
              <span className="w-2 h-2 rounded-full bg-red-500" />
              <span>Critical: {summary?.critical_count ?? findings.filter((f) => f.risk_level === 'critical').length}</span>
            </div>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-orange-50 border border-orange-200 text-xs text-orange-700 font-medium">
              <span className="w-2 h-2 rounded-full bg-orange-500" />
              <span>High: {summary?.high_count ?? findings.filter((f) => f.risk_level === 'high').length}</span>
            </div>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-700 font-medium">
              <span className="w-2 h-2 rounded-full bg-amber-500" />
              <span>Medium: {summary?.medium_count ?? findings.filter((f) => f.risk_level === 'medium').length}</span>
            </div>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 border border-slate-200 text-xs text-slate-700 font-medium">
              <span className="w-2 h-2 rounded-full bg-slate-400" />
              <span>Low: {summary?.low_count ?? findings.filter((f) => f.risk_level === 'low').length}</span>
            </div>
          </div>
        </div>

        {/* Category Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pt-3 mt-3 border-t border-gray-100 text-xs">
          {categories.map((c) => (
            <button
              key={c.key}
              onClick={() => setSelectedCategory(c.key)}
              className={`px-2.5 py-1 rounded-md whitespace-nowrap transition-colors ${
                selectedCategory === c.key
                  ? 'bg-gray-900 text-white font-medium'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200 hover:text-gray-900'
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>
      </div>

      {/* Findings List */}
      {isLoading ? (
        <div className="py-12 text-center text-xs text-gray-400">
          Loading findings & evidence...
        </div>
      ) : filteredFindings.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-xl p-8 text-center">
          <ShieldCheck size={32} className="text-emerald-500 mx-auto mb-2" />
          <h4 className="text-sm font-semibold text-gray-900">No Risk Flags Detected</h4>
          <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
            {selectedCategory !== 'all'
              ? `No terms matching the '${selectedCategory}' category were identified.`
              : 'No predatory or high-risk provisions were flagged in this document.'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredFindings.map((finding) => {
            const isExpanded = !!expandedClauses[finding.finding_id];
            const isCopied = copiedId === finding.finding_id;

            return (
              <div
                key={finding.finding_id}
                className="bg-white border border-gray-200 rounded-xl p-4 transition-all hover:border-gray-300 shadow-sm"
              >
                {/* Finding Header */}
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <RiskBadge level={finding.risk_level} />
                    <CategoryBadge category={finding.category} />
                    {finding.section && (
                      <span className="text-xs text-gray-500 font-medium">
                        Section: &ldquo;{finding.section}&rdquo;
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2 text-[11px] text-gray-400">
                    {finding.page_number && <span>Page {finding.page_number}</span>}
                    {finding.paragraph_number && <span>Para {finding.paragraph_number}</span>}
                    {finding.clause_order !== undefined && <span>Clause #{finding.clause_order + 1}</span>}
                  </div>
                </div>

                {/* Neutral Plain-Language Explanation */}
                <p className="text-xs text-gray-800 leading-relaxed font-normal mb-3">
                  {finding.explanation}
                </p>

                {/* Evidence Viewer: Exact Verbatim Original Clause */}
                <div className="border border-gray-100 rounded-lg bg-gray-50/70 p-3 text-xs">
                  <div className="flex items-center justify-between mb-1.5 text-[11px] text-gray-500">
                    <span className="font-semibold uppercase tracking-wider text-[10px] text-gray-400">
                      Verbatim Original Clause Evidence
                    </span>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleCopyText(finding.finding_id, finding.clause_text)}
                        className="flex items-center gap-1 text-[11px] text-gray-400 hover:text-gray-700 transition-colors"
                        title="Copy original clause"
                      >
                        {isCopied ? <Check size={12} className="text-emerald-600" /> : <Copy size={12} />}
                        <span>{isCopied ? 'Copied' : 'Copy'}</span>
                      </button>
                      <button
                        onClick={() => toggleClauseExpand(finding.finding_id)}
                        className="text-gray-400 hover:text-gray-700"
                        title={isExpanded ? 'Collapse clause' : 'Expand full clause'}
                      >
                        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      </button>
                    </div>
                  </div>

                  <blockquote
                    className={`font-mono text-gray-700 border-l-2 border-emerald-500 pl-2.5 text-[11.5px] leading-relaxed italic ${
                      isExpanded ? '' : 'line-clamp-3'
                    }`}
                  >
                    &ldquo;{finding.clause_text}&rdquo;
                  </blockquote>

                  {/* Ask in Chat Action Button */}
                  {onAskClause && (
                    <div className="mt-2.5 pt-2 border-t border-gray-200/60 flex justify-end">
                      <button
                        onClick={() =>
                          onAskClause(
                            `Can you analyze this ${finding.category.replace(/_/g, ' ')} clause and clarify my rights: "${finding.clause_text}"`
                          )
                        }
                        className="inline-flex items-center gap-1.5 text-[11px] font-medium text-emerald-700 hover:text-emerald-800 transition-colors"
                      >
                        <MessageSquare size={12} />
                        <span>Ask auditor about this clause</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
