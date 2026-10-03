import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, CornerDownLeft } from 'lucide-react';

export function ChatComposer({ onSend, isDisabled = false, placeholder }) {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || isDisabled) return;
    onSend(input.trim());
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [input]);

  return (
    <div className="border-t border-gray-100 bg-white/90 backdrop-blur-md px-4 py-3 md:px-8">
      <div className="max-w-3xl mx-auto">
        <form
          onSubmit={handleSubmit}
          className="relative flex items-end gap-2 bg-white border border-gray-200 rounded-2xl p-2 shadow-sm focus-within:border-gray-400 focus-within:ring-2 focus-within:ring-gray-100 transition-all"
        >
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isDisabled}
            placeholder={placeholder || 'Ask a question about this legal agreement...'}
            className="flex-1 max-h-40 px-2 py-1 text-xs md:text-sm text-gray-800 placeholder-gray-400 bg-transparent resize-none focus:outline-none leading-relaxed"
          />

          <button
            type="submit"
            disabled={isDisabled || !input.trim()}
            className="w-8 h-8 rounded-full bg-gray-900 text-white flex items-center justify-center hover:bg-gray-800 disabled:opacity-25 disabled:hover:bg-gray-900 transition-all shrink-0"
            title="Send inquiry (Enter)"
          >
            <ArrowUp size={16} />
          </button>
        </form>

        <p className="text-[11px] text-gray-400 text-center mt-2">
          Responses are generated using strictly retrieved policy clauses via pgvector semantic search.
        </p>
      </div>
    </div>
  );
}
