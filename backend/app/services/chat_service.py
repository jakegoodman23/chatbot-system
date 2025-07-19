from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from .embeddings import EmbeddingService
from .document_processor import DocumentProcessor
from .admin_service import AdminService
from .chatbot_service import ChatbotService
from ..models import ChatSession, ChatMessage, Chatbot, MessageFeedback
import uuid
import os

class ChatService:
    def __init__(self, embedding_service: EmbeddingService, document_processor: DocumentProcessor):
        self.embedding_service = embedding_service
        self.document_processor = document_processor
        self.admin_service = AdminService()
        self.chatbot_service = ChatbotService()
        self.top_k_results = int(os.getenv("TOP_K_RESULTS", 5))
    
    def get_or_create_session(self, session_id: str, chatbot_id: int, db: Session) -> ChatSession:
        """Get existing session or create new one"""
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            session = ChatSession(session_id=session_id, chatbot_id=chatbot_id)
            db.add(session)
            db.commit()
            db.refresh(session)
        return session
    
    async def generate_response(self, message: str, session_id: str, chatbot_id: int, db: Session) -> Dict[str, Any]:
        """Generate chatbot response using RAG"""
        # Get chatbot
        chatbot = self.chatbot_service.get_chatbot(db, chatbot_id)
        if not chatbot or not chatbot.is_active:
            raise ValueError(f"Chatbot with id {chatbot_id} not found or inactive")
        
        # Get or create session
        session = self.get_or_create_session(session_id, chatbot_id, db)
        
        # Search for relevant document chunks from chatbot's documents only
        similar_chunks = await self.document_processor.search_similar_chunks_for_chatbot(
            message, chatbot_id, db, self.top_k_results
        )
        
        # Build context from similar chunks
        context_texts = []
        context_chunk_ids = []
        
        for chunk, score in similar_chunks:
            if score > 0.7:  # Only include chunks with high similarity
                context_texts.append(f"From {chunk.document_filename}: {chunk.chunk_text}")
                context_chunk_ids.append(str(chunk.id))
        
        # Use chatbot's system prompt and append markdown instructions
        base_prompt = chatbot.system_prompt
        markdown_instructions = """

Format your responses using markdown for better readability:
- Use **bold** for important terms
- Use *italics* for emphasis  
- Use `code` for technical terms
- Use ## headings for sections
- Use bullet points or numbered lists when appropriate
- Use code blocks for longer code examples"""
        
        system_prompt = base_prompt + markdown_instructions
        
        context_prompt = ""
        if context_texts:
            context_prompt = "\n\nContext information:\n" + "\n\n".join(context_texts)
        
        # Prepare messages for OpenAI
        messages = [
            {"role": "system", "content": system_prompt + context_prompt},
            {"role": "user", "content": message}
        ]
        
        # Get response from OpenAI
        response = await self.embedding_service.get_chat_completion(messages)
        
        # Store chat message
        chat_message = ChatMessage(
            session_id=session_id,
            message=message,
            response=response,
            context_chunks=context_chunk_ids
        )
        db.add(chat_message)
        db.commit()
        db.refresh(chat_message)
        
        return {
            "response": response,
            "session_id": session_id,
            "context_used": len(context_chunk_ids) > 0,
            "sources": [chunk.document_filename for chunk, _ in similar_chunks if _ > 0.7],
            "message_id": chat_message.id  # Include message ID for feedback
        }
    
    def get_chat_history(self, session_id: str, db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Get chat history for a session"""
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": msg.id,
                "message": msg.message,
                "response": msg.response,
                "created_at": msg.created_at,
                "context_used": len(msg.context_chunks or []) > 0,
                "feedback": self._get_message_feedback(msg.id, db)
            }
            for msg in reversed(messages)
        ]

    def _get_message_feedback(self, message_id: int, db: Session) -> Dict[str, Any]:
        """Get feedback for a specific message"""
        feedback = db.query(MessageFeedback).filter(MessageFeedback.message_id == message_id).first()
        if feedback:
            return {
                "type": feedback.feedback_type,
                "created_at": feedback.created_at
            }
        return None

    async def submit_message_feedback(self, message_id: int, feedback_type: str, db: Session) -> MessageFeedback:
        """Submit or update feedback for a message"""
        # Verify message exists
        message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if not message:
            raise ValueError(f"Message with id {message_id} not found")
        
        # Check if feedback already exists
        existing_feedback = db.query(MessageFeedback).filter(MessageFeedback.message_id == message_id).first()
        
        if existing_feedback:
            # Update existing feedback
            existing_feedback.feedback_type = feedback_type
            existing_feedback.updated_at = func.now()
            db.commit()
            db.refresh(existing_feedback)
            return existing_feedback
        else:
            # Create new feedback
            feedback = MessageFeedback(
                message_id=message_id,
                feedback_type=feedback_type
            )
            db.add(feedback)
            db.commit()
            db.refresh(feedback)
            return feedback

    async def get_feedback_stats(self, chatbot_id: int, db: Session) -> Dict[str, Any]:
        """Get feedback statistics for a chatbot"""
        # Get all feedback for messages in sessions belonging to the chatbot
        feedback_query = db.query(MessageFeedback.feedback_type).join(
            ChatMessage, MessageFeedback.message_id == ChatMessage.id
        ).join(
            ChatSession, ChatMessage.session_id == ChatSession.session_id
        ).filter(
            ChatSession.chatbot_id == chatbot_id
        )
        
        feedback_counts = {}
        for feedback_type, in feedback_query.all():
            feedback_counts[feedback_type] = feedback_counts.get(feedback_type, 0) + 1
        
        total_feedback = sum(feedback_counts.values())
        
        return {
            "total_feedback": total_feedback,
            "thumbs_up": feedback_counts.get("thumbs_up", 0),
            "thumbs_down": feedback_counts.get("thumbs_down", 0),
            "thumbs_up_percentage": round((feedback_counts.get("thumbs_up", 0) / total_feedback * 100), 2) if total_feedback > 0 else 0,
            "thumbs_down_percentage": round((feedback_counts.get("thumbs_down", 0) / total_feedback * 100), 2) if total_feedback > 0 else 0
        }
    
    def get_session(self, session_id: str, db: Session) -> ChatSession:
        """Get session by ID"""
        return db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    
    def get_message_count(self, session_id: str, db: Session) -> int:
        """Get message count for a session"""
        return db.query(ChatMessage).filter(ChatMessage.session_id == session_id).count()
    
    def get_session_with_chatbot_info(self, session_id: str, db: Session) -> Dict[str, Any]:
        """Get session with chatbot information for deep linking"""
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            return None
        
        chatbot = self.chatbot_service.get_chatbot(db, session.chatbot_id)
        if not chatbot:
            return None
        
        message_count = self.get_message_count(session_id, db)
        
        return {
            "session_id": session.session_id,
            "chatbot_id": session.chatbot_id,
            "chatbot_name": chatbot.name,
            "chatbot_active": chatbot.is_active,
            "created_at": session.created_at,
            "message_count": message_count,
            "has_messages": message_count > 0
        }