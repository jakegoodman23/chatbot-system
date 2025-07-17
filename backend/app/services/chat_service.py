from typing import List, Dict, Any
from sqlalchemy.orm import Session
from .embeddings import EmbeddingService
from .document_processor import DocumentProcessor
from .admin_service import AdminService
from ..models import ChatSession, ChatMessage
import uuid
import os

class ChatService:
    def __init__(self, embedding_service: EmbeddingService, document_processor: DocumentProcessor):
        self.embedding_service = embedding_service
        self.document_processor = document_processor
        self.admin_service = AdminService()
        self.top_k_results = int(os.getenv("TOP_K_RESULTS", 5))
    
    def get_or_create_session(self, session_id: str, db: Session) -> ChatSession:
        """Get existing session or create new one"""
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            session = ChatSession(session_id=session_id)
            db.add(session)
            db.commit()
            db.refresh(session)
        return session
    
    async def generate_response(self, message: str, session_id: str, db: Session) -> Dict[str, Any]:
        """Generate chatbot response using RAG"""
        # Get or create session
        session = self.get_or_create_session(session_id, db)
        
        # Search for relevant document chunks
        similar_chunks = await self.document_processor.search_similar_chunks(
            message, db, self.top_k_results
        )
        
        # Build context from similar chunks
        context_texts = []
        context_chunk_ids = []
        
        for chunk, score in similar_chunks:
            if score > 0.7:  # Only include chunks with high similarity
                context_texts.append(f"From {chunk.document_filename}: {chunk.chunk_text}")
                context_chunk_ids.append(str(chunk.id))
        
        # Get configurable system prompt from admin settings and append markdown instructions
        base_prompt = self.admin_service.get_system_prompt(db)
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
        
        return {
            "response": response,
            "session_id": session_id,
            "context_used": len(context_chunk_ids) > 0,
            "sources": [chunk.document_filename for chunk, _ in similar_chunks if _ > 0.7]
        }
    
    def get_chat_history(self, session_id: str, db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Get chat history for a session"""
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.desc()).limit(limit).all()
        
        return [
            {
                "message": msg.message,
                "response": msg.response,
                "created_at": msg.created_at,
                "context_used": len(msg.context_chunks or []) > 0
            }
            for msg in reversed(messages)
        ]