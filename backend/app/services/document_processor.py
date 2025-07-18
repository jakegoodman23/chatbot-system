import os
from typing import List, Tuple
from PyPDF2 import PdfReader
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..models import Document, DocumentChunk
from .embeddings import EmbeddingService
import uuid

class DocumentProcessor:
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self.chunk_size = int(os.getenv("CHUNK_SIZE", 1000))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", 200))
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            raise
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except Exception as e:
            print(f"Error reading text file: {e}")
            raise
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end >= len(text):
                chunks.append(text[start:])
                break
            
            # Try to break at a sentence or word boundary
            chunk = text[start:end]
            last_period = chunk.rfind('.')
            last_space = chunk.rfind(' ')
            
            if last_period > len(chunk) * 0.8:  # If period is in last 20%
                end = start + last_period + 1
            elif last_space > len(chunk) * 0.8:  # If space is in last 20%
                end = start + last_space
            
            chunks.append(text[start:end])
            start = end - self.chunk_overlap
        
        return chunks
    
    async def process_document(self, file_path: str, filename: str, db: Session) -> Document:
        """Process document and store in database with embeddings"""
        file_extension = filename.lower().split('.')[-1]
        
        # Extract text based on file type
        if file_extension == 'pdf':
            content = self.extract_text_from_pdf(file_path)
            file_type = 'pdf'
        elif file_extension == 'txt':
            content = self.extract_text_from_txt(file_path)
            file_type = 'txt'
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        # Create document record
        document = Document(
            filename=filename,
            content=content,
            file_type=file_type
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Chunk the text
        chunks = self.chunk_text(content)
        
        # Get embeddings for all chunks
        embeddings = await self.embedding_service.get_embeddings_batch(chunks)
        
        # Store chunks with embeddings
        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            chunk = DocumentChunk(
                document_id=document.id,
                chunk_text=chunk_text,
                chunk_index=i,
                embedding=embedding
            )
            db.add(chunk)
        
        db.commit()
        return document
    
    async def search_similar_chunks(self, query: str, db: Session, top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        """Search for similar document chunks using vector similarity"""
        # Get query embedding
        query_embedding = await self.embedding_service.get_embedding(query)
        
        # Query for similar chunks using cosine similarity
        results = db.execute(text("""
            SELECT dc.*, d.filename, 
                   1 - (dc.embedding <=> :query_embedding) as similarity_score
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            ORDER BY dc.embedding <=> :query_embedding
            LIMIT :top_k
        """), {"query_embedding": str(query_embedding), "top_k": top_k}).fetchall()
        
        chunks_with_scores = []
        for row in results:
            chunk = DocumentChunk(
                id=row.id,
                document_id=row.document_id,
                chunk_text=row.chunk_text,
                chunk_index=row.chunk_index,
                embedding=row.embedding
            )
            chunk.document_filename = row.filename
            chunks_with_scores.append((chunk, row.similarity_score))
        
        return chunks_with_scores
    
    async def search_similar_chunks_for_chatbot(self, query: str, chatbot_id: int, db: Session, top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        """Search for similar document chunks using vector similarity, limited to chatbot's documents"""
        # Get query embedding
        query_embedding = await self.embedding_service.get_embedding(query)
        
        # Query for similar chunks using cosine similarity, filtered by chatbot's documents
        results = db.execute(text("""
            SELECT dc.*, d.filename, 
                   1 - (dc.embedding <=> :query_embedding) as similarity_score
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            JOIN chatbot_documents cd ON d.id = cd.document_id
            WHERE cd.chatbot_id = :chatbot_id
            ORDER BY dc.embedding <=> :query_embedding
            LIMIT :top_k
        """), {"query_embedding": str(query_embedding), "chatbot_id": chatbot_id, "top_k": top_k}).fetchall()
        
        chunks_with_scores = []
        for row in results:
            chunk = DocumentChunk(
                id=row.id,
                document_id=row.document_id,
                chunk_text=row.chunk_text,
                chunk_index=row.chunk_index,
                embedding=row.embedding
            )
            chunk.document_filename = row.filename
            chunks_with_scores.append((chunk, row.similarity_score))
        
        return chunks_with_scores