-- Enable the pgvector extension to work with embedding vectors
create extension if not exists vector;

-- Create documents table
create table documents (
  id uuid primary key default gen_random_uuid(),
  filename text not null,
  storage_path text not null,
  status text not null default 'Processing',
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create document_chunks table
create table document_chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid references documents(id) on delete cascade,
  page_number integer not null,
  chunk_number integer not null,
  content text not null,
  embedding vector(384) not null
);

-- Create an HNSW index for fast nearest-neighbor search based on L2 distance
create index on document_chunks using hnsw (embedding vector_l2_ops);

-- Create an RPC function for vector similarity search (required because PostgREST doesn't support vector math directly in SELECTs)
create or replace function match_document_chunks (
  query_embedding vector(384),
  match_threshold float,
  match_count int
)
returns table (
  id uuid,
  document_id uuid,
  page_number integer,
  chunk_number integer,
  content text,
  score float
)
language sql stable
as $$
  select
    document_chunks.id,
    document_chunks.document_id,
    document_chunks.page_number,
    document_chunks.chunk_number,
    document_chunks.content,
    (document_chunks.embedding <-> query_embedding) as score
  from document_chunks
  where (document_chunks.embedding <-> query_embedding) <= match_threshold
  order by document_chunks.embedding <-> query_embedding
  limit match_count;
$$;
