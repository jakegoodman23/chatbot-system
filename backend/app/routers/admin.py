from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.admin_service import AdminService
from ..services.embeddings import EmbeddingService
from ..services.document_processor import DocumentProcessor
from ..models import Document, DocumentChunk, ChatMessage, ChatSession
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import os

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBearer(auto_error=False)

# Initialize services
admin_service = AdminService()
embedding_service = EmbeddingService()
document_processor = DocumentProcessor(embedding_service)

class LoginRequest(BaseModel):
    password: str

class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    message: str

class SystemPromptRequest(BaseModel):
    prompt: str

class SettingRequest(BaseModel):
    key: str
    value: str
    description: Optional[str] = None

def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Dependency to check admin authentication"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Admin authentication required")
    
    if not admin_service.validate_session(credentials.credentials, db):
        raise HTTPException(status_code=401, detail="Invalid or expired admin session")
    
    return True

@router.post("/login", response_model=LoginResponse)
async def admin_login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """Admin login endpoint"""
    admin_service.cleanup_expired_sessions(db)
    
    if admin_service.authenticate(request.password):
        token = admin_service.create_session(db)
        return LoginResponse(
            success=True,
            token=token,
            message="Login successful"
        )
    else:
        return LoginResponse(
            success=False,
            message="Invalid password"
        )

@router.post("/logout")
async def admin_logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Admin logout endpoint"""
    if credentials:
        admin_service.invalidate_session(credentials.credentials, db)
    return {"message": "Logged out successfully"}

@router.get("/verify")
async def verify_admin(admin: bool = Depends(get_admin_user)):
    """Verify admin authentication"""
    return {"authenticated": True}

@router.get("/system-prompt")
async def get_system_prompt(
    db: Session = Depends(get_db)
):
    """Get current system prompt"""
    prompt = admin_service.get_system_prompt(db)
    return {"system_prompt": prompt}

@router.post("/system-prompt")
async def update_system_prompt(
    request: SystemPromptRequest,
    db: Session = Depends(get_db)
):
    """Update system prompt"""
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="System prompt cannot be empty")
    
    setting = admin_service.set_system_prompt(request.prompt, db)
    return {
        "message": "System prompt updated successfully",
        "system_prompt": setting.value,
        "updated_at": setting.updated_at
    }

@router.get("/settings")
async def get_all_settings(
    admin: bool = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get all admin settings"""
    settings = admin_service.get_all_settings(db)
    return {"settings": settings}

@router.post("/settings")
async def update_setting(
    request: SettingRequest,
    admin: bool = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update admin setting"""
    if not request.key.strip() or not request.value.strip():
        raise HTTPException(status_code=400, detail="Key and value cannot be empty")
    
    setting = admin_service.set_setting(request.key, request.value, db, request.description)
    return {
        "message": f"Setting '{request.key}' updated successfully",
        "setting": {
            "key": setting.key,
            "value": setting.value,
            "description": setting.description,
            "updated_at": setting.updated_at
        }
    }

@router.get("/dashboard")
async def get_dashboard_stats(
    admin: bool = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics"""
    # Get document statistics
    total_documents = db.query(Document).count()
    total_chunks = db.query(DocumentChunk).count()
    
    # Get chat statistics
    total_sessions = db.query(ChatSession).count()
    total_messages = db.query(ChatMessage).count()
    
    # Get recent documents
    recent_documents = db.query(Document).order_by(Document.created_at.desc()).limit(5).all()
    
    # Get recent chat sessions
    recent_sessions = db.query(ChatSession).order_by(ChatSession.created_at.desc()).limit(5).all()
    
    return {
        "statistics": {
            "total_documents": total_documents,
            "total_chunks": total_chunks,
            "total_sessions": total_sessions,
            "total_messages": total_messages
        },
        "recent_documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "created_at": doc.created_at,
                "chunks_count": len(doc.chunks)
            }
            for doc in recent_documents
        ],
        "recent_sessions": [
            {
                "session_id": session.session_id,
                "created_at": session.created_at,
                "message_count": len(session.messages)
            }
            for session in recent_sessions
        ]
    }

@router.get("/documents/analytics")
async def get_document_analytics(
    admin: bool = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get detailed document analytics"""
    documents = db.query(Document).all()
    
    analytics = []
    for doc in documents:
        analytics.append({
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "created_at": doc.created_at,
            "content_length": len(doc.content),
            "chunks_count": len(doc.chunks),
            "avg_chunk_length": sum(len(chunk.chunk_text) for chunk in doc.chunks) / len(doc.chunks) if doc.chunks else 0
        })
    
    return {"documents": analytics}

@router.get("/documents/{document_id}/chunks")
async def get_document_chunks(
    document_id: int,
    admin: bool = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get all chunks for a document"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index).all()
    
    return {
        "document": {
            "id": document.id,
            "filename": document.filename,
            "file_type": document.file_type,
            "created_at": document.created_at
        },
        "chunks": [
            {
                "id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "chunk_text": chunk.chunk_text,
                "created_at": chunk.created_at
            }
            for chunk in chunks
        ]
    }

@router.delete("/documents/{document_id}")
async def admin_delete_document(
    document_id: int,
    admin: bool = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Admin delete document"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    filename = document.filename
    db.delete(document)
    db.commit()
    
    return {"message": f"Document '{filename}' deleted successfully"}

@router.post("/initialize")
async def initialize_admin_settings(
    admin: bool = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Initialize default admin settings"""
    admin_service.initialize_default_settings(db)
    return {"message": "Admin settings initialized successfully"}