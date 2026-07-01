# Lumos Backend Architecture

The backend is built with **FastAPI** to provide a high-performance REST API for document ingestion and AI chat retrieval. 

## Upload Pipeline

When a user uploads a PDF (`POST /api/documents`), the backend processes it entirely within the request lifecycle:

1. **Storage**: The raw PDF is uploaded to Supabase Storage.
2. **Extraction**: `PyPDF` parses the text.
3. **Chunking**: `RecursiveCharacterTextSplitter` from LangChain breaks the text into 800-character chunks with a 150-character overlap to preserve semantic context across chunk boundaries.
4. **Embeddings**: `SentenceTransformer` (`all-MiniLM-L6-v2`) converts the textual chunks into 384-dimensional vector embeddings locally.
5. **Persistence**: The metadata is saved to the `documents` table, and the chunks (with their vectors) are batch-inserted into the `document_chunks` table in Supabase.

## RAG Pipeline

When a user asks a question (`POST /api/chat`):

1. **Query Embedding**: The user's query is converted into a vector using the exact same local `all-MiniLM-L6-v2` model.
2. **Vector Search**: The backend calls a Supabase Remote Procedure Call (RPC) to perform a cosine similarity search on `pgvector`, filtering specifically for the requested `document_id`.
3. **Generation**: The top retrieved chunks are injected into a strict prompt template. The `Groq` LLM evaluates the context and generates an answer. If the context does not contain the answer, the LLM is instructed to refuse to answer.
