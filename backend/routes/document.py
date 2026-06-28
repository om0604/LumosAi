import os
from fastapi import APIRouter, HTTPException
from config import config

router = APIRouter()

@router.post("/rebuild-index")
def rebuild_index():
    # Lazy imports to avoid loading everything unless needed
    from ingest import process_pdf
    from services.rag_service import build_index
    
    try:
        # In Phase 1, we still hardcode the local PDF for testing functionality
        pdf_path = os.path.join(config.DATA_DIR, "swiggy_annual_report.pdf")
        
        chunks = process_pdf(pdf_path)
        if not chunks:
            raise HTTPException(status_code=404, detail="PDF file not found in data directory.")
            
        build_index(chunks)
        return {"status": "success", "message": f"Successfully built index with {len(chunks)} chunks."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
