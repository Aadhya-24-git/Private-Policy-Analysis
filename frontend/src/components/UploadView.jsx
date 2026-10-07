import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, AlertCircle, ArrowRight, Loader2, Sparkles } from 'lucide-react';

const SAMPLE_TERMS = `TERMS OF SERVICE AND PRIVACY AGREEMENT

1. Subscription and Automatic Renewal
Your subscription automatically renews on a monthly basis until cancelled. You must cancel at least 30 days prior to your billing date to avoid recurring charges. Early termination penalty fees of $50 apply if cancelled before the annual term expires.

2. Additional Fees and Modifications
All fees are subject to change without prior notice. Discretionary administrative fees and late fees may be charged to your payment method.

3. Mandatory Binding Arbitration
Any disputes arising out of this agreement shall be settled through mandatory binding arbitration under JAMS rules. You agree to resolve all disputes in your individual capacity and waive any right to participate in a class action lawsuit or jury trial.

4. Data Sharing and Commercial Partnerships
We may share your personal data with third party advertising partners and commercial affiliates for targeted advertising and monetization purposes.

5. Data Retention
We retain your personal information indefinitely for analytical and business purposes, even after you delete your account.

6. Limitation of Liability
In no event shall the company be liable for any indirect, incidental, or consequential damages. Our aggregate total liability shall not exceed fifty dollars ($50).`;

export function UploadView({ onFileUpload, onTextUpload, isUploading = false, uploadError = null }) {
  const [activeTab, setActiveTab] = useState('file'); // 'file' | 'text'
  const [pastedText, setPastedText] = useState('');
  const [pastedTitle, setPastedTitle] = useState('');
  const [isDragOver, setIsDragOver] = useState(false);
  const [clientError, setClientError] = useState(null);
  const fileInputRef = useRef(null);

  const validateAndUpload = (file) => {
    setClientError(null);
    if (!file) return;

    // 1. File size check (25 MB max)
    const MAX_SIZE = 25 * 1024 * 1024;
    if (file.size === 0) {
      setClientError("The selected file is empty (0 bytes).");
      return;
    }
    if (file.size > MAX_SIZE) {
      setClientError(`File size (${(file.size / (1024 * 1024)).toFixed(1)} MB) exceeds 25 MB limit.`);
      return;
    }

    // 2. Extension check
    const allowedExtensions = ['.pdf', '.docx', '.txt'];
    const lowerName = file.name.toLowerCase();
    const hasValidExt = allowedExtensions.some((ext) => lowerName.endsWith(ext));
    if (!hasValidExt) {
      setClientError("Invalid file type. Only PDF (.pdf), Microsoft Word (.docx), and Plain Text (.txt) files are allowed.");
      return;
    }

    onFileUpload(file);
  };

  const handleFileDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndUpload(e.target.files[0]);
    }
  };

  const handleTextSubmit = (e) => {
    e.preventDefault();
    if (!pastedText.trim()) return;
    onTextUpload(pastedText.trim(), pastedTitle.trim() || 'Direct Legal Text Submission');
  };

  const handleLoadSample = () => {
    setPastedTitle('Sample Consumer Terms & Privacy Policy');
    setPastedText(SAMPLE_TERMS);
    setActiveTab('text');
  };

  return (
    <div className="max-w-2xl mx-auto px-6 py-12 flex flex-col items-center justify-center font-sans">
      {/* Hero Welcome */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-800 border border-emerald-200 mb-4">
          <Sparkles size={13} className="text-emerald-600" />
          <span>Autonomous Legal Intelligence</span>
        </div>
        <h2 className="text-2xl md:text-3xl font-bold text-gray-900 tracking-tight">
          Audit fine print for predatory risks
        </h2>
        <p className="text-sm text-gray-500 mt-2 max-w-lg mx-auto">
          Upload any Terms of Service, Privacy Policy, or EULA. The auditor segments clauses,
          detects hidden risks across 7 categories, and enables document-grounded Q&A.
        </p>
      </div>

      {/* Upload Mode Selector */}
      <div className="w-full flex justify-center mb-5">
        <div className="flex bg-gray-100 p-1 rounded-xl border border-gray-200 text-xs">
          <button
            type="button"
            onClick={() => setActiveTab('file')}
            className={`px-4 py-1.5 rounded-lg font-medium transition-all ${
              activeTab === 'file' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-800'
            }`}
          >
            Upload File (PDF / DOCX / TXT)
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('text')}
            className={`px-4 py-1.5 rounded-lg font-medium transition-all ${
              activeTab === 'text' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-800'
            }`}
          >
            Paste Plain Text
          </button>
        </div>
      </div>

      {/* Error alert */}
      {(uploadError || clientError) && (
        <div className="w-full mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700 flex items-start gap-2">
          <AlertCircle size={15} className="mt-0.5 shrink-0 text-red-500" />
          <div className="flex-1">
            <span className="font-medium">Validation error:</span> {clientError || uploadError}
          </div>
        </div>
      )}

      {/* File Upload Dropzone */}
      {activeTab === 'file' ? (
        <div className="w-full">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragOver(true);
            }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={handleFileDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`w-full border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all bg-white ${
              isDragOver
                ? 'border-emerald-500 bg-emerald-50/30'
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50/50'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={handleFileSelect}
              className="hidden"
            />

            {isUploading ? (
              <div className="py-4 flex flex-col items-center justify-center gap-3">
                <Loader2 size={32} className="text-emerald-600 animate-spin" />
                <div className="text-sm font-medium text-gray-700">
                  Ingesting document & extracting clauses...
                </div>
                <div className="text-xs text-gray-400">
                  Normalizing text and preserving source hierarchy
                </div>
              </div>
            ) : (
              <div className="py-3 flex flex-col items-center justify-center gap-2">
                <div className="w-12 h-12 rounded-full bg-emerald-50 flex items-center justify-center text-emerald-600 mb-1">
                  <UploadCloud size={24} />
                </div>
                <div className="text-sm font-medium text-gray-800">
                  Drop your legal agreement here or <span className="text-emerald-700 underline underline-offset-2">browse files</span>
                </div>
                <p className="text-xs text-gray-400">
                  Supports PDF (with page detection), DOCX, and TXT (Max 25 MB)
                </p>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Paste Plain Text Form */
        <form onSubmit={handleTextSubmit} className="w-full space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Document Title or Service Name
            </label>
            <input
              type="text"
              value={pastedTitle}
              onChange={(e) => setPastedTitle(e.target.value)}
              placeholder="e.g., Acme Cloud Terms of Service"
              className="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Legal Agreement Text
            </label>
            <textarea
              rows={8}
              value={pastedText}
              onChange={(e) => setPastedText(e.target.value)}
              placeholder="Paste full terms, privacy policy, or agreement here..."
              className="w-full px-3 py-2 text-xs font-mono border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 resize-y"
              required
            />
          </div>

          <button
            type="submit"
            disabled={isUploading || !pastedText.trim()}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gray-900 hover:bg-gray-800 text-white rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
          >
            {isUploading ? (
              <>
                <Loader2 size={15} className="animate-spin" />
                <span>Ingesting and segmenting...</span>
              </>
            ) : (
              <>
                <span>Analyze Plain Text</span>
                <ArrowRight size={15} />
              </>
            )}
          </button>
        </form>
      )}

      {/* Quick Test Sample Helper */}
      <div className="mt-8 pt-6 border-t border-gray-100 w-full text-center">
        <span className="text-xs text-gray-400 mr-2">Need a quick policy to test?</span>
        <button
          type="button"
          onClick={handleLoadSample}
          className="text-xs font-medium text-emerald-700 hover:text-emerald-800 hover:underline"
        >
          Load sample policy with hidden clauses &rarr;
        </button>
      </div>
    </div>
  );
}
