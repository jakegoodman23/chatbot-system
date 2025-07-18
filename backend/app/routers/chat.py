from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.embeddings import EmbeddingService
from ..services.document_processor import DocumentProcessor
from ..services.chat_service import ChatService
from pydantic import BaseModel
import uuid
from typing import Optional, List, Dict, Any

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize services
embedding_service = EmbeddingService()
document_processor = DocumentProcessor(embedding_service)
chat_service = ChatService(embedding_service, document_processor)

class ChatRequest(BaseModel):
    message: str
    chatbot_id: int
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    context_used: bool
    sources: List[str]

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Send a message to the chatbot"""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        result = await chat_service.generate_response(
            request.message, session_id, request.chatbot_id, db
        )
        return ChatResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

@router.get("/sessions/{session_id}/history")
async def get_chat_history(
    session_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get chat history for a session"""
    try:
        history = chat_service.get_chat_history(session_id, db, limit)
        return {
            "session_id": session_id,
            "history": history,
            "total_messages": len(history)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chat history: {str(e)}")

class SessionRequest(BaseModel):
    chatbot_id: int

@router.post("/sessions")
async def create_session(request: SessionRequest, db: Session = Depends(get_db)):
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    session = chat_service.get_or_create_session(session_id, request.chatbot_id, db)
    
    return {
        "session_id": session.session_id,
        "chatbot_id": session.chatbot_id,
        "created_at": session.created_at
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "chat"}