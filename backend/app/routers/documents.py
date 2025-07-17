from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.embeddings import EmbeddingService
from ..services.document_processor import DocumentProcessor
from ..models import Document
import os
import uuid
from typing import List

router = APIRouter(prefix="/documents", tags=["documents"])

# Initialize services
embedding_service = EmbeddingService()
document_processor = DocumentProcessor(embedding_service)

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process a document (PDF or TXT)"""
    # Validate file type
    if not file.filename.lower().endswith(('.pdf', '.txt')):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")
    
    # Create uploads directory if it doesn't exist
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save uploaded file
    file_id = str(uuid.uuid4())
    file_extension = file.filename.split('.')[-1].lower()
    file_path = os.path.join(upload_dir, f"{file_id}.{file_extension}")
    
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process document
        document = await document_processor.process_document(
            file_path, file.filename, db
        )
        
        # Clean up temporary file
        os.remove(file_path)
        
        return {
            "message": "Document uploaded and processed successfully",
            "document_id": document.id,
            "filename": document.filename,
            "chunks_created": len(document.chunks)
        }
    
    except Exception as e:
        # Clean up file if it exists
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@router.get("/")
async def list_documents(db: Session = Depends(get_db)):
    """List all uploaded documents"""
    documents = db.query(Document).all()
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "created_at": doc.created_at,
            "chunks_count": len(doc.chunks)
        }
        for doc in documents
    ]

@router.get("/{document_id}")
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get document details"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": document.id,
        "filename": document.filename,
        "file_type": document.file_type,
        "created_at": document.created_at,
        "content_preview": document.content[:500] + "..." if len(document.content) > 500 else document.content,
        "chunks_count": len(document.chunks)
    }

@router.delete("/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete a document and its chunks"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}

@router.post("/search")
async def search_documents(
    query: dict,
    db: Session = Depends(get_db)
):
    """Search for similar document chunks"""
    search_query = query.get("query", "")
    if not search_query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    try:
        similar_chunks = await document_processor.search_similar_chunks(
            search_query, db, top_k=10
        )
        
        results = []
        for chunk, score in similar_chunks:
            results.append({
                "chunk_id": chunk.id,
                "document_filename": getattr(chunk, 'document_filename', 'Unknown'),
                "chunk_text": chunk.chunk_text[:200] + "..." if len(chunk.chunk_text) > 200 else chunk.chunk_text,
                "similarity_score": round(score, 4),
                "chunk_index": chunk.chunk_index
            })
        
        return {
            "query": search_query,
            "results": results,
            "total_results": len(results)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")