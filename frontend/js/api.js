import { CONFIG } from './config.js';

async function handleResponse(res, defaultErrorMsg) {
    let data;
    try {
        data = await res.json();
    } catch (err) {
        // Handle non-JSON responses (e.g. HTML error pages from Render or 502/504 errors)
        data = null;
    }

    if (!res.ok) {
        let errorMsg = defaultErrorMsg;
        if (data && data.detail) {
            // FastAPI validation errors can be arrays, so we stringify or extract the first message
            errorMsg = Array.isArray(data.detail) ? data.detail[0].msg : data.detail;
        } else {
            // Map common HTTP status codes
            switch (res.status) {
                case 400: errorMsg = "Bad request. Please check your input."; break;
                case 401: errorMsg = "Unauthorized. Please log in."; break;
                case 403: errorMsg = "Forbidden. You don't have access."; break;
                case 404: errorMsg = "Resource not found."; break;
                case 415: errorMsg = "Unsupported media type."; break;
                case 422: errorMsg = "Validation error. Please check your data format."; break;
                case 429: errorMsg = "Too many requests. Please slow down."; break;
                case 500: errorMsg = "Internal server error. Please try again later."; break;
                case 502: errorMsg = "Bad gateway. The server is temporarily down."; break;
                case 503: errorMsg = "Service unavailable. Please try again later."; break;
                case 504: errorMsg = "Gateway timeout. The request took too long."; break;
                default: errorMsg = `HTTP Error ${res.status}: ${res.statusText || defaultErrorMsg}`;
            }
        }
        throw new Error(errorMsg);
    }
    return data;
}

export async function fetchDocuments() {
    const res = await fetch(`${CONFIG.API_BASE_URL}/documents/`);
    return handleResponse(res, "Failed to fetch documents");
}

export async function uploadDocument(file) {
    const formData = new FormData();
    formData.append("file", file);
    
    // This is synchronous (blocking) because the backend handles chunking synchronously
    const res = await fetch(`${CONFIG.API_BASE_URL}/documents/`, {
        method: "POST",
        body: formData
    });
    return handleResponse(res, "Upload failed");
}

export async function deleteDocument(id) {
    const res = await fetch(`${CONFIG.API_BASE_URL}/documents/${id}`, {
        method: "DELETE"
    });
    return handleResponse(res, "Delete failed");
}

export async function askQuestion(documentId, question) {
    const res = await fetch(`${CONFIG.API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document_id: documentId, question })
    });
    return handleResponse(res, "Failed to get answer");
}

