from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import chat, document

app = FastAPI(title="AI Document Intelligence Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register modular routes
app.include_router(chat.router, tags=["chat"])
app.include_router(document.router, tags=["document"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
