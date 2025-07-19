from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import chat, documents, admin, chatbots, human_support
from .database import engine
from .models import Base
import os

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Local Chatbot API",
    description="A RAG-based chatbot with document ingestion capabilities",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(admin.router)
app.include_router(chatbots.router)
app.include_router(human_support.router)

@app.get("/")
async def root():
    return {
        "message": "Local Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "chatbot-api"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", 8000))
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=True)