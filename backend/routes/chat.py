from fastapi import APIRouter, HTTPException
from schemas.chat import QuestionRequest, AnswerResponse, Source
from services.rag_service import retrieve, generate_answer
from config import config

router = APIRouter()

@router.post("/ask", response_model=AnswerResponse)
def ask_question(req: QuestionRequest):
    try:
        chunks = retrieve(req.question, top_k=5)
        
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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
