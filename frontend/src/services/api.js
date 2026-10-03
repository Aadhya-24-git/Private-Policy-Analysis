import { API_BASE_URL } from '../utils/constants';

const BASE = API_BASE_URL.replace(/\/+$/, '');

async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch (_) {
      // response wasn't JSON
    }
    throw new Error(errorDetail);
  }
  return response.json();
}

/**
 * 1. Health Status
 */
export async function fetchHealthStatus() {
  const startTime = performance.now();
  try {
    const res = await fetch(`${BASE}/health`, {
      headers: { 'Accept': 'application/json' },
    });
    const latencyMs = Math.round(performance.now() - startTime);
    const data = await handleResponse(res);
    return { success: true, data, latencyMs, error: null };
  } catch (err) {
    const latencyMs = Math.round(performance.now() - startTime);
    return { success: false, data: null, latencyMs, error: err.message };
  }
}

/**
 * 2. Upload Document File (PDF, DOCX, TXT)
 */
export async function uploadDocumentFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${BASE}/api/v1/analyze/file`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse(res);
}

/**
 * 3. Upload Raw Plain Text Agreement
 */
export async function uploadDocumentText(text, title = 'Direct Text Submission') {
  const res = await fetch(`${BASE}/api/v1/analyze/text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, title }),
  });
  return handleResponse(res);
}

/**
 * 4. List Uploaded Documents
 */
export async function listDocuments() {
  const res = await fetch(`${BASE}/api/v1/documents`, {
    headers: { 'Accept': 'application/json' },
  });
  return handleResponse(res);
}

/**
 * 5. Get Single Document Details
 */
export async function getDocument(documentId) {
  const res = await fetch(`${BASE}/api/v1/documents/${documentId}`, {
    headers: { 'Accept': 'application/json' },
  });
  return handleResponse(res);
}

/**
 * 6. Execute Automated Risk Rule Engine on Document
 */
export async function auditDocument(documentId) {
  const res = await fetch(`${BASE}/api/v1/documents/${documentId}/audit`, {
    method: 'POST',
    headers: { 'Accept': 'application/json' },
  });
  return handleResponse(res);
}

/**
 * 7. Retrieve Risk Findings with Source Metadata
 */
export async function getDocumentFindings(documentId) {
  const res = await fetch(`${BASE}/api/v1/documents/${documentId}/findings`, {
    headers: { 'Accept': 'application/json' },
  });
  return handleResponse(res);
}

/**
 * 8. Ask Document-Grounded Legal Question (Q&A)
 */
export async function askDocumentQuestion(documentId, question, topK = 5) {
  const res = await fetch(`${BASE}/api/v1/documents/${documentId}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, top_k: topK }),
  });
  return handleResponse(res);
}

/**
 * 9. Retrieve Chat History for Document
 */
export async function getDocumentChatHistory(documentId) {
  const res = await fetch(`${BASE}/api/v1/documents/${documentId}/chat`, {
    headers: { 'Accept': 'application/json' },
  });
  return handleResponse(res);
}

/**
 * 10. Compare Two Policy Document Versions
 */
export async function comparePolicies(oldDocumentId, newDocumentId, explainChanges = true) {
  const res = await fetch(`${BASE}/api/v1/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      old_document_id: oldDocumentId,
      new_document_id: newDocumentId,
      explain_changes: explainChanges,
    }),
  });
  return handleResponse(res);
}

