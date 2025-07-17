import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models import AdminSettings, AdminSession
from dotenv import load_dotenv

load_dotenv()

class AdminService:
    def __init__(self):
        self.admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        self.session_duration_hours = int(os.getenv("ADMIN_SESSION_DURATION", 24))
    
    def authenticate(self, password: str) -> bool:
        """Authenticate admin password"""
        return password == self.admin_password
    
    def create_session(self, db: Session) -> str:
        """Create admin session and return token"""
        # Generate secure session token
        session_token = secrets.token_urlsafe(32)
        
        # Set expiration time
        expires_at = datetime.utcnow() + timedelta(hours=self.session_duration_hours)
        
        # Create session record
        admin_session = AdminSession(
            session_token=session_token,
            expires_at=expires_at
        )
        db.add(admin_session)
        db.commit()
        
        return session_token
    
    def validate_session(self, session_token: str, db: Session) -> bool:
        """Validate admin session token"""
        if not session_token:
            return False
        
        session = db.query(AdminSession).filter(
            AdminSession.session_token == session_token,
            AdminSession.is_active == True,
            AdminSession.expires_at > datetime.utcnow()
        ).first()
        
        return session is not None
    
    def invalidate_session(self, session_token: str, db: Session) -> bool:
        """Invalidate admin session"""
        session = db.query(AdminSession).filter(
            AdminSession.session_token == session_token
        ).first()
        
        if session:
            session.is_active = False
            db.commit()
            return True
        return False
    
    def cleanup_expired_sessions(self, db: Session):
        """Clean up expired sessions"""
        db.query(AdminSession).filter(
            AdminSession.expires_at < datetime.utcnow()
        ).update({"is_active": False})
        db.commit()
    
    def get_setting(self, key: str, db: Session, default: str = None) -> Optional[str]:
        """Get admin setting value"""
        setting = db.query(AdminSettings).filter(AdminSettings.key == key).first()
        return setting.value if setting else default
    
    def set_setting(self, key: str, value: str, db: Session, description: str = None) -> AdminSettings:
        """Set admin setting value"""
        setting = db.query(AdminSettings).filter(AdminSettings.key == key).first()
        
        if setting:
            setting.value = value
            setting.updated_at = datetime.utcnow()
            if description:
                setting.description = description
        else:
            setting = AdminSettings(
                key=key,
                value=value,
                description=description
            )
            db.add(setting)
        
        db.commit()
        db.refresh(setting)
        return setting
    
    def get_all_settings(self, db: Session) -> Dict[str, Any]:
        """Get all admin settings"""
        settings = db.query(AdminSettings).all()
        return {
            setting.key: {
                "value": setting.value,
                "description": setting.description,
                "updated_at": setting.updated_at
            }
            for setting in settings
        }
    
    def get_system_prompt(self, db: Session) -> str:
        """Get current system prompt"""
        default_prompt = """You are a helpful assistant that answers questions based on the provided context. 
        Use the context information to provide accurate and relevant answers. If the context doesn't contain 
        enough information to answer the question, say so clearly. Always be truthful and don't make up information."""
        
        return self.get_setting("system_prompt", db, default_prompt)
    
    def set_system_prompt(self, prompt: str, db: Session) -> AdminSettings:
        """Set system prompt"""
        return self.set_setting(
            "system_prompt", 
            prompt, 
            db, 
            "System prompt used by the chatbot for generating responses"
        )
    
    def initialize_default_settings(self, db: Session):
        """Initialize default admin settings"""
        default_settings = [
            {
                "key": "system_prompt",
                "value": """You are a helpful assistant that answers questions based on the provided context. 
                Use the context information to provide accurate and relevant answers. If the context doesn't contain 
                enough information to answer the question, say so clearly. Always be truthful and don't make up information.""",
                "description": "System prompt used by the chatbot for generating responses (markdown formatting instructions are automatically appended)"
            },
            {
                "key": "similarity_threshold",
                "value": "0.7",
                "description": "Minimum similarity score for including document chunks in context"
            },
            {
                "key": "max_context_chunks",
                "value": "5",
                "description": "Maximum number of document chunks to include in context"
            }
        ]
        
        for setting_data in default_settings:
            existing = db.query(AdminSettings).filter(
                AdminSettings.key == setting_data["key"]
            ).first()
            
            if not existing:
                setting = AdminSettings(**setting_data)
                db.add(setting)
        
        db.commit()