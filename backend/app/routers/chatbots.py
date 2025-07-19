from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.chatbot_service import ChatbotService
from ..models import Chatbot, SuggestedQuestion
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/chatbots", tags=["chatbots"])

# Initialize service
chatbot_service = ChatbotService()

class ChatbotCreate(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: str
    settings: Optional[Dict[str, Any]] = {}

class ChatbotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class ChatbotResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    system_prompt: str
    settings: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class ChatbotStats(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    document_count: int
    chunk_count: int
    session_count: int
    created_at: str
    updated_at: str

class DocumentAssociation(BaseModel):
    document_id: int

class SuggestedQuestionCreate(BaseModel):
    question_text: str
    display_order: Optional[int] = 0

class SuggestedQuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None

class SuggestedQuestionResponse(BaseModel):
    id: int
    chatbot_id: int
    question_text: str
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

@router.get("/", response_model=List[ChatbotResponse])
async def get_chatbots(
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """Get all chatbots"""
    try:
        chatbots = chatbot_service.get_all_chatbots(db, include_inactive)
        return [
            ChatbotResponse(
                id=chatbot.id,
                name=chatbot.name,
                description=chatbot.description,
                system_prompt=chatbot.system_prompt,
                settings=chatbot.settings or {},
                is_active=chatbot.is_active,
                created_at=chatbot.created_at.isoformat(),
                updated_at=chatbot.updated_at.isoformat()
            )
            for chatbot in chatbots
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chatbots: {str(e)}")

@router.post("/", response_model=ChatbotResponse)
async def create_chatbot(
    request: ChatbotCreate,
    db: Session = Depends(get_db)
):
    """Create a new chatbot"""
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="Chatbot name cannot be empty")
    
    if not request.system_prompt.strip():
        raise HTTPException(status_code=400, detail="System prompt cannot be empty")
    
    try:
        # Check if chatbot with this name already exists
        existing = chatbot_service.get_chatbot_by_name(db, request.name)
        if existing:
            raise HTTPException(status_code=400, detail="Chatbot with this name already exists")
        
        chatbot = chatbot_service.create_chatbot(
            db=db,
            name=request.name,
            description=request.description,
            system_prompt=request.system_prompt,
            settings=request.settings
        )
        
        return ChatbotResponse(
            id=chatbot.id,
            name=chatbot.name,
            description=chatbot.description,
            system_prompt=chatbot.system_prompt,
            settings=chatbot.settings or {},
            is_active=chatbot.is_active,
            created_at=chatbot.created_at.isoformat(),
            updated_at=chatbot.updated_at.isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating chatbot: {str(e)}")

@router.get("/{chatbot_id}", response_model=ChatbotResponse)
async def get_chatbot(
    chatbot_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific chatbot"""
    try:
        chatbot = chatbot_service.get_chatbot(db, chatbot_id)
        if not chatbot:
            raise HTTPException(status_code=404, detail="Chatbot not found")
        
        return ChatbotResponse(
            id=chatbot.id,
            name=chatbot.name,
            description=chatbot.description,
            system_prompt=chatbot.system_prompt,
            settings=chatbot.settings or {},
            is_active=chatbot.is_active,
            created_at=chatbot.created_at.isoformat(),
            updated_at=chatbot.updated_at.isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chatbot: {str(e)}")

@router.put("/{chatbot_id}", response_model=ChatbotResponse)
async def update_chatbot(
    chatbot_id: int,
    request: ChatbotUpdate,
    db: Session = Depends(get_db)
):
    """Update a chatbot"""
    try:
        # Build update dictionary from non-None values
        update_data = {}
        if request.name is not None:
            if not request.name.strip():
                raise HTTPException(status_code=400, detail="Chatbot name cannot be empty")
            # Check for name conflicts
            existing = chatbot_service.get_chatbot_by_name(db, request.name)
            if existing and existing.id != chatbot_id:
                raise HTTPException(status_code=400, detail="Chatbot with this name already exists")
            update_data['name'] = request.name
        
        if request.description is not None:
            update_data['description'] = request.description
        
        if request.system_prompt is not None:
            if not request.system_prompt.strip():
                raise HTTPException(status_code=400, detail="System prompt cannot be empty")
            update_data['system_prompt'] = request.system_prompt
        
        if request.settings is not None:
            update_data['settings'] = request.settings
        
        if request.is_active is not None:
            update_data['is_active'] = request.is_active
        
        chatbot = chatbot_service.update_chatbot(db, chatbot_id, **update_data)
        if not chatbot:
            raise HTTPException(status_code=404, detail="Chatbot not found")
        
        return ChatbotResponse(
            id=chatbot.id,
            name=chatbot.name,
            description=chatbot.description,
            system_prompt=chatbot.system_prompt,
            settings=chatbot.settings or {},
            is_active=chatbot.is_active,
            created_at=chatbot.created_at.isoformat(),
            updated_at=chatbot.updated_at.isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating chatbot: {str(e)}")

@router.delete("/{chatbot_id}")
async def delete_chatbot(
    chatbot_id: int,
    db: Session = Depends(get_db)
):
    """Delete a chatbot"""
    try:
        success = chatbot_service.delete_chatbot(db, chatbot_id)
        if not success:
            raise HTTPException(status_code=404, detail="Chatbot not found")
        
        return {"message": "Chatbot deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting chatbot: {str(e)}")

@router.post("/{chatbot_id}/documents")
async def add_document_to_chatbot(
    chatbot_id: int,
    request: DocumentAssociation,
    db: Session = Depends(get_db)
):
    """Add a document to a chatbot"""
    try:
        success = chatbot_service.add_document_to_chatbot(db, chatbot_id, request.document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Chatbot or document not found")
        
        return {"message": "Document added to chatbot successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding document to chatbot: {str(e)}")

@router.delete("/{chatbot_id}/documents/{document_id}")
async def remove_document_from_chatbot(
    chatbot_id: int,
    document_id: int,
    db: Session = Depends(get_db)
):
    """Remove a document from a chatbot"""
    try:
        success = chatbot_service.remove_document_from_chatbot(db, chatbot_id, document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Chatbot or document not found")
        
        return {"message": "Document removed from chatbot successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing document from chatbot: {str(e)}")

@router.get("/{chatbot_id}/documents")
async def get_chatbot_documents(
    chatbot_id: int,
    db: Session = Depends(get_db)
):
    """Get all documents associated with a chatbot"""
    try:
        documents = chatbot_service.get_chatbot_documents(db, chatbot_id)
        return [
            {
                "id": doc.id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "created_at": doc.created_at.isoformat(),
                "chunk_count": len(doc.chunks)
            }
            for doc in documents
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chatbot documents: {str(e)}")

@router.get("/{chatbot_id}/stats", response_model=ChatbotStats)
async def get_chatbot_stats(
    chatbot_id: int,
    db: Session = Depends(get_db)
):
    """Get statistics for a chatbot"""
    try:
        stats = chatbot_service.get_chatbot_stats(db, chatbot_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Chatbot not found")
        
        return ChatbotStats(
            id=stats['id'],
            name=stats['name'],
            description=stats['description'],
            is_active=stats['is_active'],
            document_count=stats['document_count'],
            chunk_count=stats['chunk_count'],
            session_count=stats['session_count'],
            created_at=stats['created_at'].isoformat(),
            updated_at=stats['updated_at'].isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chatbot stats: {str(e)}")

@router.get("/stats/all", response_model=List[ChatbotStats])
async def get_all_chatbot_stats(db: Session = Depends(get_db)):
    """Get statistics for all chatbots"""
    try:
        stats_list = chatbot_service.get_all_chatbot_stats(db)
        return [
            ChatbotStats(
                id=stats['id'],
                name=stats['name'],
                description=stats['description'],
                is_active=stats['is_active'],
                document_count=stats['document_count'],
                chunk_count=stats['chunk_count'],
                session_count=stats['session_count'],
                created_at=stats['created_at'].isoformat(),
                updated_at=stats['updated_at'].isoformat()
            )
            for stats in stats_list
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chatbot stats: {str(e)}")

@router.post("/{chatbot_id}/activate")
async def activate_chatbot(
    chatbot_id: int,
    db: Session = Depends(get_db)
):
    """Activate a chatbot"""
    try:
        chatbot = chatbot_service.activate_chatbot(db, chatbot_id)
        if not chatbot:
            raise HTTPException(status_code=404, detail="Chatbot not found")
        
        return {"message": "Chatbot activated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error activating chatbot: {str(e)}")

@router.post("/{chatbot_id}/deactivate")
async def deactivate_chatbot(
    chatbot_id: int,
    db: Session = Depends(get_db)
):
    """Deactivate a chatbot"""
    try:
        chatbot = chatbot_service.deactivate_chatbot(db, chatbot_id)
        if not chatbot:
            raise HTTPException(status_code=404, detail="Chatbot not found")
        
        return {"message": "Chatbot deactivated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deactivating chatbot: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "chatbots"}

@router.get("/{chatbot_id}/suggested-questions", response_model=List[SuggestedQuestionResponse])
async def get_suggested_questions(chatbot_id: int, db: Session = Depends(get_db)):
    """Get all suggested questions for a chatbot"""
    chatbot = chatbot_service.get_chatbot(db, chatbot_id)
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    questions = db.query(SuggestedQuestion).filter(
        SuggestedQuestion.chatbot_id == chatbot_id,
        SuggestedQuestion.is_active == True
    ).order_by(SuggestedQuestion.display_order).all()
    
    return questions

@router.post("/{chatbot_id}/suggested-questions", response_model=SuggestedQuestionResponse)
async def create_suggested_question(
    chatbot_id: int, 
    question: SuggestedQuestionCreate, 
    db: Session = Depends(get_db)
):
    """Create a new suggested question for a chatbot"""
    chatbot = chatbot_service.get_chatbot(db, chatbot_id)
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    # If no display_order provided, set it to the next available order
    if question.display_order == 0:
        max_order = db.query(SuggestedQuestion).filter(
            SuggestedQuestion.chatbot_id == chatbot_id
        ).count()
        question.display_order = max_order + 1
    
    new_question = SuggestedQuestion(
        chatbot_id=chatbot_id,
        question_text=question.question_text,
        display_order=question.display_order
    )
    
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    
    return new_question

@router.put("/{chatbot_id}/suggested-questions/{question_id}", response_model=SuggestedQuestionResponse)
async def update_suggested_question(
    chatbot_id: int,
    question_id: int,
    question_update: SuggestedQuestionUpdate,
    db: Session = Depends(get_db)
):
    """Update a suggested question"""
    question = db.query(SuggestedQuestion).filter(
        SuggestedQuestion.id == question_id,
        SuggestedQuestion.chatbot_id == chatbot_id
    ).first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Suggested question not found")
    
    update_data = question_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)
    
    question.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(question)
    
    return question

@router.delete("/{chatbot_id}/suggested-questions/{question_id}")
async def delete_suggested_question(
    chatbot_id: int,
    question_id: int,
    db: Session = Depends(get_db)
):
    """Delete a suggested question"""
    question = db.query(SuggestedQuestion).filter(
        SuggestedQuestion.id == question_id,
        SuggestedQuestion.chatbot_id == chatbot_id
    ).first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Suggested question not found")
    
    db.delete(question)
    db.commit()
    
    return {"message": "Suggested question deleted successfully"}