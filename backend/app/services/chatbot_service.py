from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models import Chatbot, Document, ChatSession
from datetime import datetime

class ChatbotService:
    def __init__(self):
        pass
    
    def create_chatbot(self, db: Session, name: str, description: str, system_prompt: str, admin_email: str, settings: dict = None) -> Chatbot:
        """Create a new chatbot"""
        if settings is None:
            settings = {}
            
        chatbot = Chatbot(
            name=name,
            description=description,
            system_prompt=system_prompt,
            admin_email=admin_email,
            settings=settings
        )
        db.add(chatbot)
        db.commit()
        db.refresh(chatbot)
        return chatbot
    
    def get_chatbot(self, db: Session, chatbot_id: int) -> Optional[Chatbot]:
        """Get a chatbot by ID"""
        return db.query(Chatbot).filter(Chatbot.id == chatbot_id).first()
    
    def get_chatbot_by_name(self, db: Session, name: str) -> Optional[Chatbot]:
        """Get a chatbot by name"""
        return db.query(Chatbot).filter(Chatbot.name == name).first()
    
    def get_all_chatbots(self, db: Session, include_inactive: bool = False) -> List[Chatbot]:
        """Get all chatbots"""
        query = db.query(Chatbot)
        if not include_inactive:
            query = query.filter(Chatbot.is_active == True)
        return query.order_by(Chatbot.created_at.desc()).all()
    
    def update_chatbot(self, db: Session, chatbot_id: int, **kwargs) -> Optional[Chatbot]:
        """Update a chatbot"""
        chatbot = self.get_chatbot(db, chatbot_id)
        if not chatbot:
            return None
            
        for key, value in kwargs.items():
            if hasattr(chatbot, key):
                setattr(chatbot, key, value)
        
        chatbot.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(chatbot)
        return chatbot
    
    def delete_chatbot(self, db: Session, chatbot_id: int) -> bool:
        """Delete a chatbot and all associated data"""
        chatbot = self.get_chatbot(db, chatbot_id)
        if not chatbot:
            return False
            
        db.delete(chatbot)
        db.commit()
        return True
    
    def activate_chatbot(self, db: Session, chatbot_id: int) -> Optional[Chatbot]:
        """Activate a chatbot"""
        return self.update_chatbot(db, chatbot_id, is_active=True)
    
    def deactivate_chatbot(self, db: Session, chatbot_id: int) -> Optional[Chatbot]:
        """Deactivate a chatbot"""
        return self.update_chatbot(db, chatbot_id, is_active=False)
    
    def add_document_to_chatbot(self, db: Session, chatbot_id: int, document_id: int) -> bool:
        """Add a document to a chatbot"""
        chatbot = self.get_chatbot(db, chatbot_id)
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not chatbot or not document:
            return False
            
        if document not in chatbot.documents:
            chatbot.documents.append(document)
            db.commit()
        return True
    
    def remove_document_from_chatbot(self, db: Session, chatbot_id: int, document_id: int) -> bool:
        """Remove a document from a chatbot"""
        chatbot = self.get_chatbot(db, chatbot_id)
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not chatbot or not document:
            return False
            
        if document in chatbot.documents:
            chatbot.documents.remove(document)
            db.commit()
        return True
    
    def get_chatbot_documents(self, db: Session, chatbot_id: int) -> List[Document]:
        """Get all documents associated with a chatbot"""
        chatbot = self.get_chatbot(db, chatbot_id)
        if not chatbot:
            return []
        return chatbot.documents
    
    def get_chatbot_stats(self, db: Session, chatbot_id: int) -> Dict[str, Any]:
        """Get statistics for a chatbot"""
        chatbot = self.get_chatbot(db, chatbot_id)
        if not chatbot:
            return {}
        
        document_count = len(chatbot.documents)
        session_count = db.query(ChatSession).filter(ChatSession.chatbot_id == chatbot_id).count()
        
        # Count total chunks across all documents
        chunk_count = 0
        for document in chatbot.documents:
            chunk_count += len(document.chunks)
        
        return {
            "id": chatbot.id,
            "name": chatbot.name,
            "description": chatbot.description,
            "is_active": chatbot.is_active,
            "document_count": document_count,
            "chunk_count": chunk_count,
            "session_count": session_count,
            "created_at": chatbot.created_at,
            "updated_at": chatbot.updated_at
        }
    
    def get_all_chatbot_stats(self, db: Session) -> List[Dict[str, Any]]:
        """Get statistics for all chatbots"""
        chatbots = self.get_all_chatbots(db, include_inactive=True)
        return [self.get_chatbot_stats(db, chatbot.id) for chatbot in chatbots]