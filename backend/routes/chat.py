from fastapi import APIRouter, HTTPException
import logging
from schemas.chat import QuestionRequest, AnswerResponse, Source
from services.rag_service import retrieve, generate_answer
from config import config
from database import get_supabase

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/api/chat", response_model=AnswerResponse)
@router.post("/ask", response_model=AnswerResponse) # Legacy endpoint
def ask_question(req: QuestionRequest):
    """
    Query a specific document using Retrieval-Augmented Generation (RAG).
    
    Validates that the document exists and is ready, retrieves the most 
    semantically relevant chunks using vector search, and generates an 
    answer constrained to those chunks.
    """
    supabase = get_supabase()
    document_id = req.document_id
    
    if not document_id:
        raise HTTPException(status_code=400, detail="Document ID is required.")
        
    try:
        # Validate provided document exists and is ready
        doc_resp = supabase.table("documents").select("status").eq("id", document_id).execute()
        if not doc_resp.data:
            raise HTTPException(status_code=404, detail="Document not found.")
        if doc_resp.data[0]["status"] != "Ready":
            raise HTTPException(status_code=400, detail="Document is not ready for querying.")
            
        chunks = retrieve(req.question, document_id=document_id, top_k=5)
        
        # If no chunks match the similarity threshold
        if not chunks or chunks[0]['score'] > config.SIMILARITY_THRESHOLD:
            return AnswerResponse(
                answer="Insufficient information found in the provided document.",
                sources=[]
            )
            
        answer = generate_answer(req.question, chunks)
        
        sources = [
            Source(page=c['page'], content=c['content'], score=c['score']) 
            for c in chunks
        ]
        
        return AnswerResponse(
            answer=answer,
            sources=sources
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred during chat processing.")
