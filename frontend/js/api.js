import { CONFIG } from './config.js';

export async function fetchDocuments() {
    const res = await fetch(`${CONFIG.API_BASE_URL}/documents/`);
    if (!res.ok) throw new Error("Failed to fetch documents");
    return res.json();
}

export async function uploadDocument(file) {
    const formData = new FormData();
    formData.append("file", file);
    
    // This is synchronous (blocking) because the backend handles chunking synchronously
    const res = await fetch(`${CONFIG.API_BASE_URL}/documents/`, {
        method: "POST",
        body: formData
    });
    
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Upload failed");
    return data;
}

export async function deleteDocument(id) {
    const res = await fetch(`${CONFIG.API_BASE_URL}/documents/${id}`, {
        method: "DELETE"
    });
    
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Delete failed");
    return data;
}

export async function askQuestion(documentId, question) {
    const res = await fetch(`${CONFIG.API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document_id: documentId, question })
    });
    
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to get answer");
    return data;
}
