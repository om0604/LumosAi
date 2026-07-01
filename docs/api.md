# Lumos API Reference

The backend exposes a REST API powered by FastAPI.

## Base URL
`/api`

---

## Documents

### `GET /documents/`
List all uploaded documents.
- **Returns**: `200 OK`
- **Body**: Array of document objects ordered by creation date.

### `POST /documents/`
Upload and process a new PDF document.
- **Content-Type**: `multipart/form-data`
- **Body**: `file` (binary PDF file, max 25MB).
- **Returns**: `200 OK`
- **Body**: `{ "id": "uuid", "filename": "example.pdf" }`

### `DELETE /documents/{document_id}`
Delete a document entirely, cascading to its chunks and removing the file from cloud storage.
- **Returns**: `200 OK`
- **Body**: `{ "status": "success" }`

---

## Chat

### `POST /chat/`
Ask a question against a specific document.
- **Content-Type**: `application/json`
- **Body**:
  ```json
  {
    "query": "What is the revenue for 2024?",
    "document_id": "uuid-of-document"
  }
  ```
- **Returns**: `200 OK`
- **Body**:
  ```json
  {
    "answer": "The revenue for 2024 is...",
    "sources": [
      {
        "page": 4,
        "content": "...revenue was reported as...",
        "score": 0.85
      }
    ]
  }
  ```
