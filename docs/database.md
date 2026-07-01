# Lumos Database & Vector Search

Lumos leverages **Supabase PostgreSQL** extended with `pgvector` to store both document metadata and semantic chunks.

## Schema

### `documents`
Stores metadata regarding uploaded PDFs.
- `id` (UUID, Primary Key)
- `filename` (Text)
- `storage_path` (Text) - Reference to Supabase Storage bucket.
- `status` (Text) - "Processing", "Ready", or "Failed"
- `page_count` (Int)
- `chunk_count` (Int)
- `size_bytes` (BigInt)

### `document_chunks`
Stores the actual extracted text and generated embeddings.
- `id` (UUID, Primary Key)
- `document_id` (UUID, Foreign Key cascade delete to `documents`)
- `page_number` (Int)
- `chunk_number` (Int)
- `content` (Text)
- `embedding` (vector(384)) - Fits the `all-MiniLM-L6-v2` output size.

## pgvector Search (RPC)

To perform similarity search directly in the database without returning thousands of rows to the API, Lumos uses a Supabase Remote Procedure Call (RPC): `match_document_chunks`.

This SQL function computes the cosine similarity (`<=>`) between the query embedding and the chunks, strictly filtering on `document_id` to prevent cross-document contamination. It only returns chunks surpassing a provided match threshold.
