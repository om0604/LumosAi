from typing import List, Dict, Any
import threading
import logging
from groq import Groq
from config import config
from database import get_supabase

logger = logging.getLogger(__name__)

# Lazy-loading singleton state for the embedding model
_embedder = None
_embedder_lock = threading.Lock()

def get_embedder() -> Any:
    """
    Lazy-load the SentenceTransformer embedding model in a thread-safe manner.
    This prevents the model from loading during application startup (saving memory)
    and defers loading until the first request that requires embeddings.
    """
    global _embedder
    if _embedder is None:
        with _embedder_lock:
            # Double-checked locking to avoid race conditions across threads
            if _embedder is None:
                try:
                    logger.info("Importing and initializing SentenceTransformer model (lazy-loaded)...")
                    from sentence_transformers import SentenceTransformer
                    _embedder = SentenceTransformer('all-MiniLM-L6-v2')
                    logger.info("SentenceTransformer model initialized successfully.")
                except Exception as e:
                    logger.error(f"Failed to load embedding model: {e}")
                    raise RuntimeError("Embedding model failed to initialize.") from e
    return _embedder

def build_index(chunks: List[Dict[str, Any]], document_id: str) -> None:
    """
    Generate embeddings for document chunks and insert them into the Supabase database.
    
    Args:
        chunks: List of dictionaries containing page number and text content.
        document_id: The UUID of the document these chunks belong to.
    """
    logger.info(f"[Document: {document_id}] Loading embedding model")
    embedder = get_embedder()
    logger.info(f"[Document: {document_id}] Embedding model loaded")
    
    logger.info(f"[Document: {document_id}] Encoding {len(chunks)} chunks")
    texts = [chunk['content'] for chunk in chunks]
    embeddings = embedder.encode(texts, show_progress_bar=False)
    logger.info(f"[Document: {document_id}] Encoding finished")
    
    logger.info(f"[Document: {document_id}] Writing embeddings")
    supabase = get_supabase()
    batch_size = 50
    total_batches = (len(chunks) + batch_size - 1) // batch_size
    
    # Insert in batches to prevent huge HTTP payloads
    for i in range(0, len(chunks), batch_size):
        batch_num = (i // batch_size) + 1
        batch_chunks = chunks[i:i + batch_size]
        batch_embeddings = embeddings[i:i + batch_size]
        
        data = []
        for j, chunk in enumerate(batch_chunks):
            data.append({
                "document_id": document_id,
                "page_number": chunk['page'],
                "chunk_number": i + j,
                "content": chunk['content'],
                "embedding": batch_embeddings[j].tolist()
            })
        
        supabase.table("document_chunks").insert(data).execute()
        logger.info(f"[Document: {document_id}] Inserted batch {batch_num}/{total_batches}")
        
    import gc
    del embeddings
    gc.collect()

def retrieve(query: str, document_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieve nearest neighbor chunks via Supabase pgvector RPC.
    
    Args:
        query: The user's question.
        document_id: The UUID of the document to search within.
        top_k: Number of most relevant chunks to return.
        
    Returns:
        List of relevant contexts with page numbers and relevance scores.
    """
    supabase = get_supabase()
    
    embedder = get_embedder()
    query_embedding = embedder.encode([query])[0].tolist()
    
    response = supabase.rpc(
        "match_document_chunks",
        {
            "query_embedding": query_embedding,
            "match_threshold": config.SIMILARITY_THRESHOLD,
            "match_count": top_k,
            "filter_document_id": document_id
        }
    ).execute()
    
    results = []
    for item in response.data:
        results.append({
            "page": item["page_number"],
            "content": item["content"],
            "score": item["score"]
        })
            
    return results

def generate_answer(query: str, contexts: List[Dict[str, Any]]) -> str:
    """
    Generate an answer using Groq LLM based strictly on the provided context.
    
    Args:
        query: The user's question.
        contexts: List of retrieved text chunks from the document.
        
    Returns:
        The generated answer string.
    """
    prompt_template = """You are an AI Document Assistant.

Answer the question ONLY using the provided context.
If the answer is not found in the context, respond:
"The answer is not available in the provided document."

Context:
{context}

Question:
{question}

Answer:"""
    
    context_text = "\n\n".join([f"Page {c['page']}:\n{c['content']}" for c in contexts])
    formatted_prompt = prompt_template.format(context=context_text, question=query)
    
    try:
        client = Groq(api_key=config.GROQ_API_KEY)
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": formatted_prompt}],
            model=config.GROQ_MODEL,
            temperature=0,
            max_tokens=500,
        )
        return chat_completion.choices[0].message.content
        
    except Exception as e:
        return f"Error connecting to Groq API: {str(e)}"
