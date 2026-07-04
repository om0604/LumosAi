import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import config
from routes import chat, documents
from database import get_supabase

# Validate configuration at startup — fail fast if secrets are missing
config.validate()

logger = logging.getLogger(__name__)

app = FastAPI(title="Lumos — AI Document Intelligence Platform")


@app.get("/api/health")
def health_check():
    """
    Lightweight health check that verifies database connectivity
    and configuration status for all external services.
    """
    db_status = "disconnected"
    storage_status = "configured" if config.SUPABASE_BUCKET else "missing_bucket"
    embedding_status = "configured" if config.JINA_API_KEY else "missing_key"
    llm_status = "configured" if config.GROQ_API_KEY else "missing_key"

    try:
        supabase = get_supabase()
        supabase.table("documents").select("id").limit(1).execute()
        db_status = "connected"
    except Exception as e:
        logger.warning(f"Health check — database probe failed: {e}")

    all_ok = (
        db_status == "connected"
        and storage_status == "configured"
        and embedding_status == "configured"
        and llm_status == "configured"
    )

    return {
        "status": "healthy" if all_ok else "degraded",
        "database": db_status,
        "storage": storage_status,
        "embedding_provider": embedding_status,
        "llm_provider": llm_status,
    }


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://lumos-ai-ten.vercel.app",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register modular routes
app.include_router(chat.router, tags=["chat"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
