import React, { useState } from 'react';
import { User, Sparkles, FileText, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';

export function ChatStream({
  messages = [],
  isGenerating = false,
  error = null,
  onPromptSelect,
  documentTitle = 'this policy',
}) {
  const [expandedSources, setExpandedSources] = useState({});

  const toggleSourceExpand = (msgIndex, sourceIndex) => {
    const key = `${msgIndex}-${sourceIndex}`;
    setExpandedSources((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const SUGGESTED_PROMPTS = [
    'Does this subscription renew automatically, and how do I cancel?',
    'Does this company share or sell my personal data with third parties?',
    'Does this agreement mandate binding arbitration or waive jury trials?',
    'What liability limitations or warranty disclaimers are in this contract?',
  ];

  return (
    <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 max-w-3xl w-full mx-auto font-sans">
      {messages.length === 0 ? (
        /* Empty Conversation State */
        <div className="py-12 text-center">
          <div className="w-12 h-12 rounded-2xl bg-emerald-50 border border-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-4 shadow-sm">
            <Sparkles size={22} />
          </div>
          <h3 className="text-base font-semibold text-gray-900">
            Ask the Fine Print Auditor
          </h3>
          <p className="text-xs text-gray-500 mt-1 max-w-md mx-auto">
            All answers are strictly grounded in the extracted clauses of{' '}
            <span className="font-medium text-gray-700">{documentTitle}</span> via pgvector semantic search.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-6 max-w-xl mx-auto text-left">
            {SUGGESTED_PROMPTS.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => onPromptSelect(prompt)}
                className="p-3 rounded-xl border border-gray-200 bg-white hover:bg-gray-50 text-xs text-gray-700 text-left transition-all hover:border-gray-300 shadow-sm"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      ) : (
        /* Message Stream */
        <div className="space-y-6">
          {messages.map((msg, idx) => {
            const isUser = msg.role === 'user';

            return (
              <div
                key={idx}
                className={`flex gap-3 text-xs md:text-sm ${
                  isUser ? 'justify-end' : 'justify-start'
                }`}
              >
                {!isUser && (
                  <div className="w-7 h-7 rounded-lg bg-emerald-600 text-white flex items-center justify-center shrink-0 mt-0.5 shadow-sm text-xs font-bold">
                    §
                  </div>
                )}

                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                    isUser
                      ? 'bg-gray-900 text-white rounded-br-sm'
                      : 'bg-white border border-gray-200 text-gray-800 rounded-bl-sm shadow-sm'
                  }`}
                >
                  {/* Message Content */}
                  <div className="whitespace-pre-wrap leading-relaxed text-xs md:text-sm">
                    {msg.content}
                  </div>

                  {/* Grounded Citation Sources (for AI responses) */}
                  {!isUser && msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <div className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2">
                        Retrieved Policy Citations ({msg.sources.length})
                      </div>
                      <div className="space-y-1.5">
                        {msg.sources.map((src, sIdx) => {
                          const isExpanded = !!expandedSources[`${idx}-${sIdx}`];
                          return (
                            <div
                              key={sIdx}
                              className="rounded-lg border border-gray-100 bg-gray-50/80 p-2 text-xs"
                            >
                              <div
                                onClick={() => toggleSourceExpand(idx, sIdx)}
                                className="flex items-center justify-between cursor-pointer select-none text-[11px] font-medium text-gray-600 hover:text-gray-900"
                              >
                                <div className="flex items-center gap-1.5 truncate">
                                  <FileText size={12} className="text-emerald-600 shrink-0" />
                                  <span className="font-semibold">
                                    Clause #{src.clause_order + 1}
                                  </span>
                                  {src.section && (
                                    <span className="text-gray-400 truncate">
                                      &bull; {src.section}
                                    </span>
                                  )}
                                  {src.page_number && (
                                    <span className="text-gray-400">
                                      &bull; Page {src.page_number}
                                    </span>
                                  )}
                                </div>
                                <span className="text-gray-400">
                                  {isExpanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                                </span>
                              </div>

                              {isExpanded && (
                                <blockquote className="mt-2 pl-2 border-l-2 border-emerald-500 font-mono text-[11px] text-gray-600 italic">
                                  &ldquo;{src.clause_text}&rdquo;
                                </blockquote>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Timestamp */}
                  {msg.timestamp && (
                    <div
                      className={`text-[10px] mt-1.5 text-right ${
                        isUser ? 'text-gray-400' : 'text-gray-400'
                      }`}
                    >
                      {new Date(msg.timestamp).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </div>
                  )}
                </div>

                {isUser && (
                  <div className="w-7 h-7 rounded-lg bg-gray-200 text-gray-700 flex items-center justify-center shrink-0 mt-0.5 text-xs font-medium">
                    <User size={14} />
                  </div>
                )}
              </div>
            );
          })}

          {/* Thinking / In-Flight State */}
          {isGenerating && (
            <div className="flex gap-3 text-xs justify-start">
              <div className="w-7 h-7 rounded-lg bg-emerald-600 text-white flex items-center justify-center shrink-0 shadow-sm text-xs font-bold">
                §
              </div>
              <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm flex items-center gap-2 text-gray-500">
                <span className="inline-flex gap-1 items-center">
                  <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce" />
                  <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce [animation-delay:0.2s]" />
                  <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce [animation-delay:0.4s]" />
                </span>
                <span className="text-xs">Auditing policy clauses...</span>
              </div>
            </div>
          )}

          {/* Error Banner */}
          {error && (
            <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700 flex items-start gap-2">
              <AlertCircle size={15} className="mt-0.5 shrink-0 text-red-500" />
              <div>
                <span className="font-semibold">Audit Q&amp;A error:</span> {error}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
