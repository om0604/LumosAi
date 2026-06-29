import { state } from './state.js';
import { formatBytes, formatDate, escapeHTML } from './helpers.js';

export function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? '<i data-lucide="check-circle"></i>' : '<i data-lucide="alert-circle"></i>';
    toast.innerHTML = `${icon} <span>${escapeHTML(message)}</span>`;
    
    container.appendChild(toast);
    if (window.lucide) window.lucide.createIcons();
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

export function renderDocumentList(onSelect, onDelete) {
    const container = document.getElementById('document-list');
    container.innerHTML = '';
    
    if (state.documents.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted text-sm" style="padding: 24px 0;">
                No documents uploaded yet.
            </div>
        `;
        return;
    }
    
    state.documents.forEach(doc => {
        const card = document.createElement('div');
        card.className = `doc-card ${state.currentDocumentId === doc.id ? 'active' : ''}`;
        card.onclick = () => onSelect(doc.id);
        
        let statusClass = 'badge-processing';
        if (doc.status === 'Ready') statusClass = 'badge-ready';
        if (doc.status === 'Failed') statusClass = 'badge-failed';
        
        card.innerHTML = `
            <div class="doc-title">
                <i data-lucide="file-text" style="width: 16px; height: 16px;"></i>
                <span class="truncate" title="${escapeHTML(doc.filename)}">${escapeHTML(doc.filename)}</span>
            </div>
            <div class="doc-meta">
                <span>${formatBytes(doc.size_bytes)} • ${doc.page_count} pages</span>
                <span class="badge ${statusClass}">${doc.status}</span>
            </div>
            <div class="flex justify-between items-center" style="margin-top: 4px;">
                <span class="text-xs text-muted">${formatDate(doc.created_at)}</span>
                <button class="btn btn-danger delete-btn" data-id="${doc.id}" style="padding: 4px; font-size: 14px;">
                    <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i>
                </button>
            </div>
        `;
        
        container.appendChild(card);
    });
    
    // Add delete listeners
    container.querySelectorAll('.delete-btn').forEach(btn => {
        btn.onclick = (e) => {
            e.stopPropagation();
            onDelete(btn.dataset.id);
        };
    });
    
    if (window.lucide) window.lucide.createIcons();
}

export function renderChatHeader() {
    const header = document.getElementById('chat-header');
    const doc = state.getCurrentDocument();
    
    if (!doc) {
        header.innerHTML = `
            <div class="flex items-center gap-sm text-muted">
                <i data-lucide="inbox"></i>
                <span>No document selected</span>
            </div>
        `;
    } else {
        header.innerHTML = `
            <div class="flex items-center gap-sm">
                <i data-lucide="file-text" class="text-muted"></i>
                <span style="font-weight: 600;">${escapeHTML(doc.filename)}</span>
                <span class="badge badge-ready" style="margin-left: 8px;">Ready</span>
            </div>
        `;
    }
    
    if (window.lucide) window.lucide.createIcons();
}

export function toggleEmptyState(show) {
    document.getElementById('chat-empty-state').classList.toggle('hidden', !show);
    document.getElementById('chat-history').classList.toggle('hidden', show);
}

export function appendUserMessage(text) {
    const container = document.getElementById('chat-history');
    const msg = document.createElement('div');
    msg.className = 'message user';
    msg.innerHTML = `
        <div class="message-bubble">
            ${escapeHTML(text)}
        </div>
    `;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
}

export function appendAssistantMessage(answer, sources) {
    const container = document.getElementById('chat-history');
    const msg = document.createElement('div');
    msg.className = 'message assistant';
    
    // Parse Markdown if marked is available
    const parsedAnswer = window.marked ? window.marked.parse(answer) : escapeHTML(answer);
    
    let sourcesHTML = '';
    if (sources && sources.length > 0) {
        sourcesHTML = `
            <div class="sources-container">
                <div class="text-xs text-muted" style="margin-bottom: 8px; font-weight: 600; text-transform: uppercase;">Sources</div>
                ${sources.map((s, i) => `
                    <div class="source-card">
                        <div class="source-header" onclick="this.nextElementSibling.classList.toggle('open')">
                            <span>Page ${s.page} • Score: ${(s.score).toFixed(2)}</span>
                            <i data-lucide="chevron-down" style="width: 14px; height: 14px;"></i>
                        </div>
                        <div class="source-body">
                            ${escapeHTML(s.content)}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    msg.innerHTML = `
        <div class="message-bubble w-full">
            ${parsedAnswer}
            ${sourcesHTML}
        </div>
    `;
    
    // Remove loading skeleton if present
    const skeleton = document.getElementById('chat-skeleton');
    if (skeleton) skeleton.remove();
    
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
    if (window.lucide) window.lucide.createIcons();
}

export function appendSkeletonLoader() {
    const container = document.getElementById('chat-history');
    const msg = document.createElement('div');
    msg.className = 'message assistant';
    msg.id = 'chat-skeleton';
    msg.innerHTML = `
        <div class="message-bubble w-full" style="padding: 16px;">
            <div class="skeleton skeleton-text"></div>
            <div class="skeleton skeleton-text"></div>
            <div class="skeleton skeleton-text short"></div>
        </div>
    `;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
}

export function setUploadLoading(isLoading) {
    const btn = document.getElementById('upload-btn');
    const icon = document.getElementById('upload-icon');
    if (isLoading) {
        btn.disabled = true;
        icon.outerHTML = '<i data-lucide="loader" id="upload-icon" class="spinner"></i>';
    } else {
        btn.disabled = false;
        icon.outerHTML = '<i data-lucide="upload" id="upload-icon"></i>';
    }
    if (window.lucide) window.lucide.createIcons();
}
