import os
from fastapi import APIRouter, HTTPException
from config import config
from database import get_supabase
from storage import upload_file_to_storage

router = APIRouter()

@router.post("/rebuild-index")
def rebuild_index():
    # Lazy imports to avoid loading everything unless needed
    from ingest import process_pdf
    from services.rag_service import build_index
    
    supabase = get_supabase()
    
    try:
        # 1. We look for any PDF in the data directory for testing single-document behavior
        pdf_filename = None
        for file in os.listdir(config.DATA_DIR):
            if file.endswith(".pdf"):
                pdf_filename = file
                break
                
        if not pdf_filename:
            raise HTTPException(status_code=404, detail="No PDF file found in data directory.")
            
        pdf_path = os.path.join(config.DATA_DIR, pdf_filename)
        
        # 2. Extract chunks
        chunks = process_pdf(pdf_path)
        if not chunks:
            raise HTTPException(status_code=404, detail="PDF file not found in data directory.")
            
        # 3. Upload to Supabase Storage
        storage_path = f"reports/{pdf_filename}"
        upload_file_to_storage(pdf_path, storage_path)
        
        # 4. Clear existing rows in documents to maintain the single-document MVP behavior
        supabase.table("documents").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        
        # 5. Insert document metadata row
        doc_insert = supabase.table("documents").insert({
            "filename": pdf_filename,
            "storage_path": storage_path,
            "status": "Processing"
        }).execute()
        
        document_id = doc_insert.data[0]["id"]
            
        # 6. Build index (inserts chunks)
        build_index(chunks, document_id)
        
        # 7. Update status to Ready
        supabase.table("documents").update({"status": "Ready"}).eq("id", document_id).execute()
        
        return {"status": "success", "message": f"Successfully migrated {len(chunks)} chunks to Supabase."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
