from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, ARRAY, Boolean, JSON, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from pgvector.sqlalchemy import Vector

Base = declarative_base()

# Association table for many-to-many relationship between chatbots and documents
chatbot_documents = Table(
    'chatbot_documents',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('chatbot_id', Integer, ForeignKey('chatbots.id', ondelete='CASCADE'), nullable=False),
    Column('document_id', Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
    Column('created_at', DateTime, default=datetime.utcnow)
)

class Chatbot(Base):
    __tablename__ = "chatbots"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)
    system_prompt = Column(Text, nullable=False)
    settings = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Many-to-many relationship with documents
    documents = relationship("Document", secondary=chatbot_documents, back_populates="chatbots")
    # One-to-many relationship with chat sessions
    chat_sessions = relationship("ChatSession", back_populates="chatbot", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    file_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    # Many-to-many relationship with chatbots
    chatbots = relationship("Chatbot", secondary=chatbot_documents, back_populates="documents")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Vector(1536))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    document = relationship("Document", back_populates="chunks")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    chatbot_id = Column(Integer, ForeignKey("chatbots.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    chatbot = relationship("Chatbot", back_populates="chat_sessions")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"))
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    context_chunks = Column(ARRAY(String))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("ChatSession", back_populates="messages")

class AdminSettings(Base):
    __tablename__ = "admin_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AdminSession(Base):
    __tablename__ = "admin_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)