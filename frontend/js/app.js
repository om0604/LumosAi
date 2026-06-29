import { state } from './state.js';
import * as api from './api.js';
import * as ui from './ui.js';

async function loadDocuments() {
    try {
        const docs = await api.fetchDocuments();
        state.setDocuments(docs);
        ui.renderDocumentList(handleSelectDocument, handleDeleteDocument);
        
        // Auto-select newest ready document if none selected
        if (!state.currentDocumentId && docs.length > 0) {
            const readyDoc = docs.find(d => d.status === 'Ready');
            if (readyDoc) {
                handleSelectDocument(readyDoc.id);
            }
        }
    } catch (e) {
        ui.showToast(e.message, 'error');
    }
}

async function handleUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    // Reset file input
    e.target.value = '';
    
    ui.setUploadLoading(true);
    ui.showToast("Uploading and processing document... this may take a moment.", 'success');
    
    try {
        await api.uploadDocument(file);
        ui.showToast("Document successfully processed!", 'success');
        await loadDocuments();
    } catch (e) {
        ui.showToast(e.message, 'error');
    } finally {
        ui.setUploadLoading(false);
    }
}

async function handleDeleteDocument(id) {
    if (!confirm("Are you sure you want to delete this document?")) return;
    
    try {
        await api.deleteDocument(id);
        ui.showToast("Document deleted.", 'success');
        
        if (state.currentDocumentId === id) {
            state.setCurrentDocument(null);
            ui.renderChatHeader();
            ui.toggleEmptyState(true);
        }
        
        await loadDocuments();
    } catch (e) {
        ui.showToast(e.message, 'error');
    }
}

function handleSelectDocument(id) {
    state.setCurrentDocument(id);
    ui.renderDocumentList(handleSelectDocument, handleDeleteDocument); // Re-render to show active state
    ui.renderChatHeader();
    ui.toggleEmptyState(false);
    
    // Clear chat history on switch
    document.getElementById('chat-history').innerHTML = '';
}

async function handleSendMessage() {
    if (!state.currentDocumentId) {
        ui.showToast("Please select a document first.", 'error');
        return;
    }
    
    const input = document.getElementById('chat-input');
    const question = input.value.trim();
    if (!question) return;
    
    input.value = '';
    ui.appendUserMessage(question);
    ui.appendSkeletonLoader();
    
    try {
        const data = await api.askQuestion(state.currentDocumentId, question);
        ui.appendAssistantMessage(data.answer, data.sources);
    } catch (e) {
        // Remove skeleton and show error
        const skeleton = document.getElementById('chat-skeleton');
        if (skeleton) skeleton.remove();
        ui.showToast(e.message, 'error');
    }
}

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Bind events
    document.getElementById('file-upload').addEventListener('change', handleUpload);
    document.getElementById('upload-btn').addEventListener('click', () => document.getElementById('file-upload').click());
    
    document.getElementById('chat-send-btn').addEventListener('click', handleSendMessage);
    document.getElementById('chat-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSendMessage();
    });
    
    document.getElementById('mobile-menu-btn').addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('open');
    });
    
    // Initialize Lucide Icons
    if (window.lucide) window.lucide.createIcons();
    
    // Load initial data
    loadDocuments();
});
