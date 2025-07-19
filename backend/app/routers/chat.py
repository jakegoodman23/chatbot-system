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
    message_id: int  # Add message_id for feedback functionality

class FeedbackRequest(BaseModel):
    message_id: int
    feedback_type: str  # 'thumbs_up' or 'thumbs_down'

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
    """Get chat history for a session with metadata"""
    try:
        session = chat_service.get_session(session_id, db)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        history = chat_service.get_chat_history(session_id, db, limit)
        total_count = chat_service.get_message_count(session_id, db)
        
        return {
            "session_id": session_id,
            "chatbot_id": session.chatbot_id,
            "history": history,
            "total_messages": total_count,
            "returned_messages": len(history),
            "created_at": session.created_at
        }
    
    except HTTPException:
        raise
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

@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get session details for deep linking"""
    try:
        session = chat_service.get_session(session_id, db)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session.session_id,
            "chatbot_id": session.chatbot_id,
            "created_at": session.created_at,
            "message_count": chat_service.get_message_count(session_id, db)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving session: {str(e)}")

@router.get("/sessions/{session_id}/info")
async def get_session_info(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get session and chatbot info for deep linking validation"""
    try:
        session_info = chat_service.get_session_with_chatbot_info(session_id, db)
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session_info
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving session info: {str(e)}")

@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """Submit thumbs up/down feedback for a chat message"""
    if request.feedback_type not in ['thumbs_up', 'thumbs_down']:
        raise HTTPException(status_code=400, detail="Invalid feedback type. Must be 'thumbs_up' or 'thumbs_down'")
    
    try:
        result = await chat_service.submit_message_feedback(
            request.message_id, request.feedback_type, db
        )
        return {"message": "Feedback submitted successfully", "feedback_id": result.id}
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")

@router.get("/feedback/stats/{chatbot_id}")
async def get_feedback_stats(
    chatbot_id: int,
    db: Session = Depends(get_db)
):
    """Get feedback statistics for a chatbot"""
    try:
        stats = await chat_service.get_feedback_stats(chatbot_id, db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting feedback stats: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "chat"}