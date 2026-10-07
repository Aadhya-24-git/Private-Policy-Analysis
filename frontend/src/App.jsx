import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { DocumentHeader } from './components/DocumentHeader';
import { UploadView } from './components/UploadView';
import { FindingsList } from './components/FindingsList';
import { ChatStream } from './components/ChatStream';
import { ChatComposer } from './components/ChatComposer';
import { SettingsModal } from './components/SettingsModal';
import { PolicyCompareView } from './components/PolicyCompareView';
import { useHealth } from './hooks/useHealth';
import {
  uploadDocumentFile,
  uploadDocumentText,
  listDocuments,
  getDocument,
  auditDocument,
  getDocumentFindings,
  askDocumentQuestion,
  getDocumentChatHistory,
  comparePolicies,
} from './services/api';

const LOCAL_STORAGE_KEY = 'fine_print_auditor_recent_docs';

export function App() {
  const { healthData, latencyMs, loading: healthLoading, error: healthError, refresh: refreshHealth } = useHealth(30000);
  const backendConnected = !healthError && healthData?.status === 'healthy';

  // State
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [selectedDocument, setSelectedDocument] = useState(null);

  // Tab & View State
  const [viewMode, setViewMode] = useState('policy'); // 'policy' | 'compare'
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' | 'findings'
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Policy Comparison State
  const [comparisonData, setComparisonData] = useState(null);
  const [isComparing, setIsComparing] = useState(false);
  const [compareError, setCompareError] = useState(null);

  // Upload State
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  // Audit & Findings State
  const [findings, setFindings] = useState([]);
  const [findingsSummary, setFindingsSummary] = useState(null);
  const [isAuditing, setIsAuditing] = useState(false);
  const [findingsLoading, setFindingsLoading] = useState(false);

  // Chat State
  const [chatMessages, setChatMessages] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [chatError, setChatError] = useState(null);

  /**
   * Load documents on initial mount
   */
  const loadDocuments = useCallback(async () => {
    try {
      const serverDocs = await listDocuments();
      if (Array.isArray(serverDocs) && serverDocs.length > 0) {
        setDocuments(serverDocs);
        localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(serverDocs));
      } else {
        // Fallback to local storage if server list empty
        const cached = localStorage.getItem(LOCAL_STORAGE_KEY);
        if (cached) {
          try {
            setDocuments(JSON.parse(cached));
          } catch (_) {}
        }
      }
    } catch (_) {
      const cached = localStorage.getItem(LOCAL_STORAGE_KEY);
      if (cached) {
        try {
          setDocuments(JSON.parse(cached));
        } catch (_) {}
      }
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  /**
   * Load Document Details, Findings, and Chat History when a document is selected
   */
  const selectDocument = useCallback(async (docId) => {
    setViewMode('policy');
    setSelectedDocId(docId);
    setUploadError(null);
    setChatError(null);
    setFindingsLoading(true);

    try {
      // 1. Fetch document metadata
      const doc = await getDocument(docId);
      setSelectedDocument(doc);

      // 2. Fetch stored findings
      try {
        const findingsData = await getDocumentFindings(docId);
        setFindings(findingsData.findings || []);
        setFindingsSummary(findingsData);
      } catch (err) {
        console.warn('Failed to fetch findings:', err);
        setFindings([]);
        setFindingsSummary(null);
      }

      // 3. Fetch chat history
      try {
        const historyData = await getDocumentChatHistory(docId);
        if (Array.isArray(historyData)) {
          const formattedHistory = [];
          historyData.forEach((item) => {
            formattedHistory.push({
              role: 'user',
              content: item.question,
              timestamp: item.created_at,
            });
            formattedHistory.push({
              role: 'assistant',
              content: item.answer,
              timestamp: item.created_at,
              sources: [],
            });
          });
          setChatMessages(formattedHistory);
        }
      } catch (err) {
        console.warn('Failed to fetch chat history:', err);
        setChatMessages([]);
      }
    } catch (err) {
      console.error('Error selecting document:', err);
    } finally {
      setFindingsLoading(false);
    }
  }, []);

  /**
   * Start New Policy
   */
  const handleNewPolicy = () => {
    setViewMode('policy');
    setSelectedDocId(null);
    setSelectedDocument(null);
    setFindings([]);
    setFindingsSummary(null);
    setChatMessages([]);
    setUploadError(null);
    setChatError(null);
    setActiveTab('chat');
  };

  /**
   * Execute semantic comparison between two policies
   */
  const handleRunCompare = async (oldDocId, newDocId) => {
    if (!oldDocId || !newDocId || oldDocId === newDocId) return;
    setIsComparing(true);
    setCompareError(null);
    setComparisonData(null);
    try {
      const result = await comparePolicies(oldDocId, newDocId, true);
      setComparisonData(result);
    } catch (err) {
      setCompareError(err.message || 'Comparison failed');
      setComparisonData(null);
    } finally {
      setIsComparing(false);
    }
  };

  const handleClearComparison = () => {
    setComparisonData(null);
    setCompareError(null);
  };

  /**
   * Execute automated risk rule audit on current document
   */
  const handleRunAudit = async () => {
    if (!selectedDocId || isAuditing) return;
    setIsAuditing(true);
    try {
      const summaryData = await auditDocument(selectedDocId);
      setFindings(summaryData.findings || []);
      setFindingsSummary(summaryData);
      setActiveTab('findings');
    } catch (err) {
      alert(`Audit failed: ${err.message}`);
    } finally {
      setIsAuditing(false);
    }
  };

  /**
   * Handle File Upload (PDF, DOCX, TXT)
   */
  const handleFileUpload = async (file) => {
    setIsUploading(true);
    setUploadError(null);

    try {
      const result = await uploadDocumentFile(file);
      const newDoc = {
        document_id: result.document_id,
        filename: result.filename,
        source_type: result.source_type,
        status: result.status,
        total_clauses: result.total_clauses,
        upload_time: new Date().toISOString(),
      };

      // Update documents list
      const updatedDocs = [newDoc, ...documents.filter((d) => d.document_id !== newDoc.document_id)];
      setDocuments(updatedDocs);
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(updatedDocs));

      // Select newly uploaded document
      setSelectedDocId(newDoc.document_id);
      setSelectedDocument(newDoc);

      // Automatically run automated risk audit
      try {
        const auditRes = await auditDocument(newDoc.document_id);
        setFindings(auditRes.findings || []);
        setFindingsSummary(auditRes);
      } catch (_) {
        // If background audit fails, user can run it manually
      }

      setChatMessages([]);
    } catch (err) {
      setUploadError(err.message || 'File upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  /**
   * Handle Raw Text Upload
   */
  const handleTextUpload = async (text, title) => {
    setIsUploading(true);
    setUploadError(null);

    try {
      const result = await uploadDocumentText(text, title);
      const newDoc = {
        document_id: result.document_id,
        filename: result.filename,
        source_type: result.source_type,
        status: result.status,
        total_clauses: result.total_clauses,
        upload_time: new Date().toISOString(),
      };

      const updatedDocs = [newDoc, ...documents.filter((d) => d.document_id !== newDoc.document_id)];
      setDocuments(updatedDocs);
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(updatedDocs));

      setSelectedDocId(newDoc.document_id);
      setSelectedDocument(newDoc);

      try {
        const auditRes = await auditDocument(newDoc.document_id);
        setFindings(auditRes.findings || []);
        setFindingsSummary(auditRes);
      } catch (_) {}

      setChatMessages([]);
    } catch (err) {
      setUploadError(err.message || 'Text upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  /**
   * Send Question to Document-Grounded Q&A Endpoint
   */
  const handleSendMessage = async (question) => {
    if (!selectedDocId || !question.trim() || isGenerating) return;

    const userMessage = {
      role: 'user',
      content: question.trim(),
      timestamp: new Date().toISOString(),
    };

    setChatMessages((prev) => [...prev, userMessage]);
    setIsGenerating(true);
    setChatError(null);

    try {
      const response = await askDocumentQuestion(selectedDocId, question.trim());

      const assistantMessage = {
        role: 'assistant',
        content: response.answer,
        sources: response.sources || [],
        timestamp: response.created_at || new Date().toISOString(),
      };

      setChatMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setChatError(err.message || 'Failed to retrieve grounded answer');
    } finally {
      setIsGenerating(false);
    }
  };

  /**
   * Ask question triggered from Finding Evidence Viewer
   */
  const handleAskClause = (prompt) => {
    setActiveTab('chat');
    handleSendMessage(prompt);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-white text-gray-900 font-sans">
      {/* Left Sidebar */}
      <Sidebar
        documents={documents}
        selectedDocId={selectedDocId}
        onSelectDoc={selectDocument}
        onNewPolicy={handleNewPolicy}
        onOpenCompare={() => {
          setViewMode('compare');
          setComparisonData(null);
          setCompareError(null);
        }}
        viewMode={viewMode}
        onOpenSettings={() => setIsSettingsOpen(true)}
        backendConnected={backendConnected}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      {/* Main Workspace Area */}
      <main className="flex-1 flex flex-col h-full overflow-hidden bg-[#fafafa]">
        {viewMode === 'compare' ? (
          <div className="flex-1 overflow-y-auto">
            <PolicyCompareView
              documents={documents}
              onCompare={handleRunCompare}
              onClearComparison={handleClearComparison}
              comparisonData={comparisonData}
              isComparing={isComparing}
              error={compareError}
              initialOldDocId={selectedDocId || (documents.length > 1 ? documents[1].document_id : '')}
              initialNewDocId={
                documents.length > 0
                  ? selectedDocId === documents[0].document_id && documents.length > 1
                    ? documents[1].document_id
                    : documents[0].document_id
                  : ''
              }
            />
          </div>
        ) : selectedDocId && selectedDocument ? (
          <>
            {/* Document Header */}
            <DocumentHeader
              document={selectedDocument}
              findingsCount={findings.length}
              activeTab={activeTab}
              onTabChange={setActiveTab}
              onRunAudit={handleRunAudit}
              isAuditing={isAuditing}
            />

            {/* Tab 1: Auditor Q&A Conversation */}
            {activeTab === 'chat' && (
              <div className="flex-1 flex flex-col overflow-hidden">
                <ChatStream
                  messages={chatMessages}
                  isGenerating={isGenerating}
                  error={chatError}
                  onPromptSelect={handleSendMessage}
                  documentTitle={selectedDocument?.filename || 'this policy'}
                />

                <ChatComposer
                  onSend={handleSendMessage}
                  isDisabled={isGenerating}
                  placeholder={`Ask anything about "${selectedDocument.filename || 'this policy'}"...`}
                />
              </div>
            )}

            {/* Tab 2: Risk Findings & Evidence Viewer */}
            {activeTab === 'findings' && (
              <div className="flex-1 overflow-y-auto">
                <FindingsList
                  findings={findings}
                  summary={findingsSummary}
                  onAskClause={handleAskClause}
                  isLoading={findingsLoading || isAuditing}
                />
              </div>
            )}
          </>
        ) : (
          /* Empty / Upload View */
          <div className="flex-1 overflow-y-auto flex items-center justify-center p-4">
            <UploadView
              onFileUpload={handleFileUpload}
              onTextUpload={handleTextUpload}
              isUploading={isUploading}
              uploadError={uploadError}
            />
          </div>
        )}
      </main>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        healthData={healthData}
        latencyMs={latencyMs}
        isLoading={healthLoading}
        error={healthError}
        onRefresh={refreshHealth}
      />
    </div>
  );
}

export default App;
