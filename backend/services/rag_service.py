from typing import List, Dict, Any
import logging
from groq import Groq
from config import config
from database import get_supabase
from services import embedding_service

logger = logging.getLogger(__name__)


def build_index(chunks: List[Dict[str, Any]], document_id: str) -> None:
    """
    Generate embeddings for document chunks via Jina AI and insert them
    into the Supabase pgvector database.

    Args:
        chunks: List of dicts with 'page' and 'content' keys.
        document_id: UUID of the owning document.
    """
    texts = [chunk['content'] for chunk in chunks]

    logger.info(f"[Document: {document_id}] Requesting embeddings for {len(texts)} chunks")
    embeddings = embedding_service.embed(texts, task="retrieval.passage")
    logger.info(f"[Document: {document_id}] Embeddings received")

    logger.info(f"[Document: {document_id}] Writing embeddings to Supabase")
    supabase = get_supabase()
    batch_size = 50
    total_batches = (len(chunks) + batch_size - 1) // batch_size

    for i in range(0, len(chunks), batch_size):
        batch_num = (i // batch_size) + 1
        batch_chunks = chunks[i:i + batch_size]
        batch_embeddings = embeddings[i:i + batch_size]

        data = [
            {
                "document_id": document_id,
                "page_number": chunk['page'],
                "chunk_number": i + j,
                "content": chunk['content'],
                "embedding": batch_embeddings[j],   # already a plain list[float]
            }
            for j, chunk in enumerate(batch_chunks)
        ]

        supabase.table("document_chunks").insert(data).execute()
        logger.info(f"[Document: {document_id}] Inserted batch {batch_num}/{total_batches}")

    logger.info(f"[Document: {document_id}] All embeddings written successfully")


def retrieve(query: str, document_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Embed the user query via Jina AI, then run a nearest-neighbour search
    against pgvector using the Supabase RPC.

    Args:
        query: The user's question.
        document_id: UUID of the document to search within.
        top_k: Maximum number of chunks to return.

    Returns:
        List of relevant chunks with page numbers and relevance scores.
    """
    query_embeddings = embedding_service.embed([query], task="retrieval.query")
    query_embedding = query_embeddings[0]

    supabase = get_supabase()
    response = supabase.rpc(
        "match_document_chunks",
        {
            "query_embedding": query_embedding,
            "match_threshold": config.SIMILARITY_THRESHOLD,
            "match_count": top_k,
            "filter_document_id": document_id,
        },
    ).execute()

    return [
        {
            "page": item["page_number"],
            "content": item["content"],
            "score": item["score"],
        }
        for item in response.data
    ]


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
