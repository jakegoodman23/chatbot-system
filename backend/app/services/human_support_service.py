from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from ..models import HumanSupportRequest, HumanSupportMessage, Chatbot, ChatSession
from .email_service import EmailService
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class HumanSupportService:
    def __init__(self):
        self.email_service = EmailService()
    
    def create_support_request(
        self,
        chatbot_id: int,
        session_id: str,
        initial_message: str,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Create a new human support request"""
        try:
            # Generate unique request ID
            request_id = str(uuid.uuid4())
            
            # Get chatbot info for email notification
            chatbot = db.query(Chatbot).filter(Chatbot.id == chatbot_id).first()
            if not chatbot:
                raise ValueError(f"Chatbot with ID {chatbot_id} not found")
            
            # Create support request
            support_request = HumanSupportRequest(
                request_id=request_id,
                chatbot_id=chatbot_id,
                session_id=session_id,
                user_name=user_name,
                user_email=user_email,
                initial_message=initial_message,
                status="pending"
            )
            
            db.add(support_request)
            db.commit()
            db.refresh(support_request)
            
            # Send email notification to admin
            self.email_service.send_human_support_notification(
                admin_email=chatbot.admin_email,
                chatbot_name=chatbot.name,
                user_message=initial_message,
                support_request_id=request_id,
                user_name=user_name,
                user_email=user_email
            )
            
            # Send confirmation to user if email provided
            if user_email:
                self.email_service.send_user_confirmation(
                    user_email=user_email,
                    chatbot_name=chatbot.name,
                    support_request_id=request_id
                )
            
            logger.info(f"Created human support request {request_id} for chatbot {chatbot.name}")
            
            return {
                "request_id": request_id,
                "status": "pending",
                "message": "Your request for human support has been submitted. An agent will join the conversation shortly."
            }
            
        except Exception as e:
            logger.error(f"Error creating support request: {str(e)}")
            raise
    
    def get_support_request(self, request_id: str, db: Session) -> Optional[HumanSupportRequest]:
        """Get a support request by ID"""
        return db.query(HumanSupportRequest).filter(
            HumanSupportRequest.request_id == request_id
        ).first()
    
    def get_pending_requests(self, chatbot_id: Optional[int] = None, db: Session = None) -> List[HumanSupportRequest]:
        """Get all pending support requests, optionally filtered by chatbot"""
        query = db.query(HumanSupportRequest).filter(
            HumanSupportRequest.status == "pending"
        )
        
        if chatbot_id:
            query = query.filter(HumanSupportRequest.chatbot_id == chatbot_id)
        
        return query.order_by(desc(HumanSupportRequest.created_at)).all()
    
    def get_active_requests(self, chatbot_id: Optional[int] = None, db: Session = None) -> List[HumanSupportRequest]:
        """Get all active support requests, optionally filtered by chatbot"""
        query = db.query(HumanSupportRequest).filter(
            HumanSupportRequest.status == "active"
        )
        
        if chatbot_id:
            query = query.filter(HumanSupportRequest.chatbot_id == chatbot_id)
        
        return query.order_by(desc(HumanSupportRequest.updated_at)).all()
    
    def join_support_request(self, request_id: str, db: Session) -> Dict[str, Any]:
        """Admin joins a support request"""
        try:
            support_request = self.get_support_request(request_id, db)
            if not support_request:
                raise ValueError(f"Support request {request_id} not found")
            
            if support_request.status != "pending":
                raise ValueError(f"Support request {request_id} is not pending")
            
            # Update status to active
            support_request.status = "active"
            support_request.admin_joined_at = datetime.utcnow()
            support_request.updated_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Admin joined support request {request_id}")
            
            return {
                "request_id": request_id,
                "status": "active",
                "message": "Successfully joined the conversation"
            }
            
        except Exception as e:
            logger.error(f"Error joining support request: {str(e)}")
            raise
    
    def add_message(
        self,
        request_id: str,
        sender_type: str,
        message: str,
        db: Session
    ) -> Dict[str, Any]:
        """Add a message to a support request"""
        try:
            support_request = self.get_support_request(request_id, db)
            if not support_request:
                raise ValueError(f"Support request {request_id} not found")
            
            if support_request.status not in ["active", "pending"]:
                raise ValueError(f"Cannot add message to {support_request.status} request")
            
            # Create message
            support_message = HumanSupportMessage(
                support_request_id=support_request.id,
                sender_type=sender_type,
                message=message
            )
            
            db.add(support_message)
            
            # Update support request timestamp
            support_request.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(support_message)
            
            return {
                "message_id": support_message.id,
                "sender_type": sender_type,
                "message": message,
                "created_at": support_message.created_at.isoformat(),
                "request_id": request_id
            }
            
        except Exception as e:
            logger.error(f"Error adding message to support request: {str(e)}")
            raise
    
    def get_messages(self, request_id: str, db: Session) -> List[Dict[str, Any]]:
        """Get all messages for a support request"""
        support_request = self.get_support_request(request_id, db)
        if not support_request:
            return []
        
        messages = db.query(HumanSupportMessage).filter(
            HumanSupportMessage.support_request_id == support_request.id
        ).order_by(HumanSupportMessage.created_at).all()
        
        return [
            {
                "id": msg.id,
                "sender_type": msg.sender_type,
                "message": msg.message,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    
    def resolve_support_request(self, request_id: str, db: Session) -> Dict[str, Any]:
        """Mark a support request as resolved"""
        try:
            support_request = self.get_support_request(request_id, db)
            if not support_request:
                raise ValueError(f"Support request {request_id} not found")
            
            support_request.status = "resolved"
            support_request.resolved_at = datetime.utcnow()
            support_request.updated_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Support request {request_id} marked as resolved")
            
            return {
                "request_id": request_id,
                "status": "resolved",
                "message": "Support request has been resolved"
            }
            
        except Exception as e:
            logger.error(f"Error resolving support request: {str(e)}")
            raise
    
    def close_support_request(self, request_id: str, db: Session) -> Dict[str, Any]:
        """Mark a support request as closed"""
        try:
            support_request = self.get_support_request(request_id, db)
            if not support_request:
                raise ValueError(f"Support request {request_id} not found")
            
            support_request.status = "closed"
            support_request.updated_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Support request {request_id} marked as closed")
            
            return {
                "request_id": request_id,
                "status": "closed",
                "message": "Support request has been closed"
            }
            
        except Exception as e:
            logger.error(f"Error closing support request: {str(e)}")
            raise
    
    def get_support_request_details(self, request_id: str, db: Session) -> Optional[Dict[str, Any]]:
        """Get detailed information about a support request"""
        support_request = self.get_support_request(request_id, db)
        if not support_request:
            return None
        
        return {
            "request_id": support_request.request_id,
            "chatbot_id": support_request.chatbot_id,
            "chatbot_name": support_request.chatbot.name if support_request.chatbot else None,
            "session_id": support_request.session_id,
            "user_name": support_request.user_name,
            "user_email": support_request.user_email,
            "initial_message": support_request.initial_message,
            "status": support_request.status,
            "admin_joined_at": support_request.admin_joined_at.isoformat() if support_request.admin_joined_at else None,
            "resolved_at": support_request.resolved_at.isoformat() if support_request.resolved_at else None,
            "created_at": support_request.created_at.isoformat(),
            "updated_at": support_request.updated_at.isoformat(),
            "messages": self.get_messages(request_id, db)
        }