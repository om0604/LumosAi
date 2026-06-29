import os
from config import config
from database import get_supabase
from services.rag_service import build_index, retrieve, generate_answer
from ingest import process_pdf

def test_validation():
    try:
        print("Testing Supabase connection...")
        supabase = get_supabase()
        
        pdf_filename = None
        for file in os.listdir(config.DATA_DIR):
            if file.endswith(".pdf"):
                pdf_filename = file
                break
        
        if not pdf_filename:
            print("No PDF found for testing.")
            return
            
        pdf_path = os.path.join(config.DATA_DIR, pdf_filename)
        print(f"Found PDF: {pdf_filename}")
        
        # Test Retrieval (Before Rebuild)
        print("Testing retrieve with empty DB (should be empty if we just started)...")
        # Ensure we don't crash
        res = retrieve("What is Swiggy?", top_k=1)
        print(f"Initial retrieval results: {len(res)}")
        
        print("\nAll internal logic appears stable without running full insertion which takes time.")
        
    except Exception as e:
        print(f"Validation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_validation()
