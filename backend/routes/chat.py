from fastapi import APIRouter, HTTPException
import time
import logging
from schemas.chat import QuestionRequest, AnswerResponse, Source
from services.rag_service import retrieve, generate_answer
from config import config
from database import get_supabase

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/api/chat", response_model=AnswerResponse)
def ask_question(req: QuestionRequest):
    """
    Query a specific document using Retrieval-Augmented Generation (RAG).

    Validates that the document exists and is ready, retrieves the most
    semantically relevant chunks using vector search, and generates an
    answer constrained to those chunks.
    """
    document_id = req.document_id
    logger.info(f"[Chat] Request received — document_id={document_id}")
    request_start = time.time()

    if not document_id:
        raise HTTPException(status_code=400, detail="Document ID is required.")

    supabase = get_supabase()

    try:
        # Validate provided document exists and is ready
        doc_resp = supabase.table("documents").select("status").eq("id", document_id).execute()
        if not doc_resp.data:
            raise HTTPException(status_code=404, detail="Document not found.")

        doc_status = doc_resp.data[0]["status"]
        if doc_status == "Processing":
            raise HTTPException(status_code=400, detail="Document is still processing. Please wait.")
        if doc_status != "Ready":
            raise HTTPException(status_code=400, detail=f"Document is not ready for querying (status: {doc_status}).")

        # Retrieve relevant chunks
        retrieval_start = time.time()
        chunks = retrieve(req.question, document_id=document_id, top_k=5)
        logger.info(f"[Chat] Retrieval completed — chunks={len(chunks)}, duration={time.time() - retrieval_start:.2f}s")

        # If no chunks match the similarity threshold
        if not chunks or chunks[0]['score'] > config.SIMILARITY_THRESHOLD:
            return AnswerResponse(
                answer="Insufficient information found in the provided document.",
                sources=[]
            )

        # Generate answer
        answer_start = time.time()
        answer = generate_answer(req.question, chunks)
        logger.info(f"[Chat] Answer generated — duration={time.time() - answer_start:.2f}s")

        sources = [
            Source(page=c['page'], content=c['content'], score=c['score'])
            for c in chunks
        ]

        total_time = time.time() - request_start
        logger.info(f"[Chat] Request completed — total_duration={total_time:.2f}s")

        return AnswerResponse(
            answer=answer,
            sources=sources
        )

    except HTTPException:
        raise
    except RuntimeError as e:
        # RuntimeError is raised by embedding_service or generate_answer for API failures
        logger.error(f"[Chat] Service error: {e}")
        error_msg = str(e)
        if "Jina" in error_msg:
            raise HTTPException(status_code=502, detail="Embedding generation failed. Please try again.")
        if "Groq" in error_msg:
            raise HTTPException(status_code=502, detail="Answer generation failed. The LLM service may be temporarily unavailable.")
        raise HTTPException(status_code=500, detail="An external service error occurred during chat processing.")
    except Exception as e:
        logger.error(f"[Chat] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred during chat processing.")
