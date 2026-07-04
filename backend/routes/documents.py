from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
import io
import time
import os
import gc
import logging
from database import get_supabase
from ingest import process_pdf
from services.rag_service import build_index
from storage import upload_bytes_to_storage, delete_file_from_storage, download_file_from_storage

router = APIRouter()
logger = logging.getLogger(__name__)

# Maximum upload size in bytes (25 MB)
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


def process_document_background(document_id: str, storage_path: str, safe_filename: str):
    """
    Heavy processing executed as a FastAPI BackgroundTask after the upload
    endpoint has already returned HTTP 200.

    Stages:
      1. Download PDF from Supabase Storage
      2. Extract text and chunk it
      3. Generate embeddings via Jina AI
      4. Insert embeddings into pgvector
      5. Update document status to Ready

    Any unhandled exception marks the document as Failed so it never
    stays stuck in Processing.
    """
    logger.info("========== Document Processing Started ==========")
    logger.info(f"[Document: {document_id}] Filename: {safe_filename}")
    logger.info(f"[Document: {document_id}] Storage Path: {storage_path}")
    pipeline_start = time.time()

    supabase = get_supabase()

    try:
        # ── Stage 1: Download ────────────────────────────────────────────
        logger.info(f"[Document: {document_id}] Stage: PDF Download")
        stage_start = time.time()
        try:
            file_bytes = download_file_from_storage(storage_path)
        except Exception:
            logger.exception(f"[Document: {document_id}] Failed to download PDF from storage.")
            raise
        logger.info(f"[Document: {document_id}] Stage: PDF Download — Duration: {time.time() - stage_start:.2f}s")

        # ── Stage 2: Extract text and chunk ─────────────────────────────
        logger.info(f"[Document: {document_id}] Stage: PDF Extraction and Chunking")
        stage_start = time.time()
        try:
            pdf_stream = io.BytesIO(file_bytes)
            chunks, page_count = process_pdf(pdf_stream)
        except Exception:
            logger.exception(f"[Document: {document_id}] Failed during PDF extraction and chunking.")
            raise
        logger.info(
            f"[Document: {document_id}] Stage: PDF Extraction and Chunking — "
            f"Duration: {time.time() - stage_start:.2f}s, "
            f"pages={page_count}, chunks={len(chunks)}"
        )

        if not chunks:
            raise ValueError("PDF contains no extractable text.")

        # ── Stage 3 & 4: Embed and insert ────────────────────────────────
        logger.info(f"[Document: {document_id}] Stage: Embedding Generation and Database Insertion")
        stage_start = time.time()
        try:
            build_index(chunks, document_id)
        except Exception:
            logger.exception(f"[Document: {document_id}] Failed during embedding generation and database insertion.")
            raise
        logger.info(
            f"[Document: {document_id}] Stage: Embedding Generation and Database Insertion — "
            f"Duration: {time.time() - stage_start:.2f}s"
        )

        # ── Stage 5: Update metadata ──────────────────────────────────────
        logger.info(f"[Document: {document_id}] Stage: Metadata Update")
        stage_start = time.time()
        try:
            supabase.table("documents").update({
                "status": "Ready",
                "page_count": page_count,
                "chunk_count": len(chunks),
            }).eq("id", document_id).execute()
        except Exception:
            logger.exception(f"[Document: {document_id}] Failed to update document metadata to Ready.")
            raise
        logger.info(f"[Document: {document_id}] Stage: Metadata Update — Duration: {time.time() - stage_start:.2f}s")

        # ── Cleanup ───────────────────────────────────────────────────────
        del chunks, file_bytes, pdf_stream
        gc.collect()

        total_time = time.time() - pipeline_start
        logger.info(f"[Document: {document_id}] Total processing time: {total_time:.2f}s")
        logger.info("========== Document Processing Finished ==========")

    except Exception:
        logger.error(f"[Document: {document_id}] Processing failed. Marking document as Failed.")
        try:
            supabase.table("documents").update({"status": "Failed"}).eq("id", document_id).execute()
        except Exception as db_e:
            logger.error(f"[Document: {document_id}] Could not set status to Failed: {db_e}")


@router.get("/")
def get_documents():
    """List all uploaded documents ordered by creation date."""
    supabase = get_supabase()
    try:
        response = supabase.table("documents").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch documents. The database may be temporarily unavailable.")


@router.post("/")
def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload a new PDF document, extract text, generate embeddings, and store in database."""
    safe_filename = os.path.basename(file.filename)

    if not safe_filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Unsupported file type. Only PDF is allowed.")

    file_bytes = file.file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    size_bytes = len(file_bytes)
    if size_bytes > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 25 MB.")

    supabase = get_supabase()
    timestamp = int(time.time())
    storage_path = f"reports/{timestamp}_{safe_filename}"

    try:
        doc_insert = supabase.table("documents").insert({
            "filename": safe_filename,
            "storage_path": storage_path,
            "status": "Processing",
            "size_bytes": size_bytes,
            "file_type": file.content_type or "application/pdf"
        }).execute()

        document_id = doc_insert.data[0]["id"]
    except Exception as e:
        logger.error(f"Database insert error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create document record.")

    try:
        upload_bytes_to_storage(file_bytes, storage_path, content_type=file.content_type or "application/pdf")

        background_tasks.add_task(process_document_background, document_id, storage_path, safe_filename)

        return {"id": document_id, "filename": safe_filename}

    except Exception as e:
        logger.error(f"Storage upload error: {e}")
        try:
            supabase.table("documents").update({"status": "Failed"}).eq("id", document_id).execute()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail="Failed to upload file to storage.")


@router.delete("/{document_id}")
def delete_document(document_id: str):
    """Delete a document, its chunks (via DB cascade), and the Storage file."""
    supabase = get_supabase()

    try:
        doc_resp = supabase.table("documents").select("storage_path").eq("id", document_id).execute()
        if not doc_resp.data:
            raise HTTPException(status_code=404, detail="Document not found.")

        storage_path = doc_resp.data[0]["storage_path"]

        try:
            delete_file_from_storage(storage_path)
        except Exception as e:
            logger.warning(f"Failed to delete from storage {storage_path}: {e}")

        supabase.table("documents").delete().eq("id", document_id).execute()
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database delete error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document.")
