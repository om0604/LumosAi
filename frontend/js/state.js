export const state = {
    documents: [],
    currentDocumentId: null,
    isUploading: false,
    isChatting: false,

    setDocuments(docs) {
        this.documents = docs;
    },

    setCurrentDocument(id) {
        this.currentDocumentId = id;
    },

    getCurrentDocument() {
        return this.documents.find(d => d.id === this.currentDocumentId);
    }
};
