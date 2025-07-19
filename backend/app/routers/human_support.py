from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.human_support_service import HumanSupportService
from ..services.admin_service import admin_required
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/human-support", tags=["human-support"])

# Initialize service
human_support_service = HumanSupportService()

class SupportRequestCreate(BaseModel):
    chatbot_id: int
    session_id: str
    initial_message: str
    user_name: Optional[str] = None
    user_email: Optional[str] = None

class SupportMessageCreate(BaseModel):
    message: str
    sender_type: str  # 'user' or 'admin'

class SupportRequestResponse(BaseModel):
    request_id: str
    status: str
    message: str

class SupportRequestDetails(BaseModel):
    request_id: str
    chatbot_id: int
    chatbot_name: Optional[str]
    session_id: str
    user_name: Optional[str]
    user_email: Optional[str]
    initial_message: str
    status: str
    admin_joined_at: Optional[str]
    resolved_at: Optional[str]
    created_at: str
    updated_at: str
    messages: List[Dict[str, Any]]

# WebSocket connection manager for real-time communication
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, request_id: str):
        await websocket.accept()
        if request_id not in self.active_connections:
            self.active_connections[request_id] = []
        self.active_connections[request_id].append(websocket)
        logger.info(f"WebSocket connected for support request {request_id}")
    
    def disconnect(self, websocket: WebSocket, request_id: str):
        if request_id in self.active_connections:
            self.active_connections[request_id].remove(websocket)
            if not self.active_connections[request_id]:
                del self.active_connections[request_id]
        logger.info(f"WebSocket disconnected for support request {request_id}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str, request_id: str):
        if request_id in self.active_connections:
            for connection in self.active_connections[request_id]:
                try:
                    await connection.send_text(message)
                except:
                    # Remove dead connections
                    self.active_connections[request_id].remove(connection)

manager = ConnectionManager()

@router.post("/request", response_model=SupportRequestResponse)
async def create_support_request(
    request: SupportRequestCreate,
    db: Session = Depends(get_db)
):
    """Create a new human support request"""
    try:
        result = human_support_service.create_support_request(
            chatbot_id=request.chatbot_id,
            session_id=request.session_id,
            initial_message=request.initial_message,
            user_name=request.user_name,
            user_email=request.user_email,
            db=db
        )
        return SupportRequestResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/requests/pending")
async def get_pending_requests(
    chatbot_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(admin_required)
):
    """Get all pending support requests"""
    try:
        requests = human_support_service.get_pending_requests(chatbot_id, db)
        return [
            {
                "request_id": req.request_id,
                "chatbot_id": req.chatbot_id,
                "chatbot_name": req.chatbot.name if req.chatbot else None,
                "user_name": req.user_name,
                "user_email": req.user_email,
                "initial_message": req.initial_message,
                "created_at": req.created_at.isoformat()
            }
            for req in requests
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/requests/active")
async def get_active_requests(
    chatbot_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(admin_required)
):
    """Get all active support requests"""
    try:
        requests = human_support_service.get_active_requests(chatbot_id, db)
        return [
            {
                "request_id": req.request_id,
                "chatbot_id": req.chatbot_id,
                "chatbot_name": req.chatbot.name if req.chatbot else None,
                "user_name": req.user_name,
                "user_email": req.user_email,
                "initial_message": req.initial_message,
                "admin_joined_at": req.admin_joined_at.isoformat() if req.admin_joined_at else None,
                "updated_at": req.updated_at.isoformat()
            }
            for req in requests
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/requests/{request_id}", response_model=SupportRequestDetails)
async def get_support_request_details(
    request_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed information about a support request"""
    try:
        details = human_support_service.get_support_request_details(request_id, db)
        if not details:
            raise HTTPException(status_code=404, detail="Support request not found")
        
        return SupportRequestDetails(**details)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/requests/{request_id}/join")
async def join_support_request(
    request_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(admin_required)
):
    """Admin joins a support request"""
    try:
        result = human_support_service.join_support_request(request_id, db)
        
        # Notify connected users via WebSocket
        await manager.broadcast(
            json.dumps({
                "type": "admin_joined",
                "message": "A support agent has joined the conversation",
                "request_id": request_id
            }),
            request_id
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/requests/{request_id}/resolve")
async def resolve_support_request(
    request_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(admin_required)
):
    """Mark a support request as resolved"""
    try:
        result = human_support_service.resolve_support_request(request_id, db)
        
        # Notify connected users via WebSocket
        await manager.broadcast(
            json.dumps({
                "type": "request_resolved",
                "message": "This support request has been resolved",
                "request_id": request_id
            }),
            request_id
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/requests/{request_id}/close")
async def close_support_request(
    request_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(admin_required)
):
    """Mark a support request as closed"""
    try:
        result = human_support_service.close_support_request(request_id, db)
        
        # Notify connected users via WebSocket
        await manager.broadcast(
            json.dumps({
                "type": "request_closed",
                "message": "This support request has been closed",
                "request_id": request_id
            }),
            request_id
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/requests/{request_id}/messages")
async def add_message(
    request_id: str,
    message: SupportMessageCreate,
    db: Session = Depends(get_db)
):
    """Add a message to a support request"""
    try:
        result = human_support_service.add_message(
            request_id=request_id,
            sender_type=message.sender_type,
            message=message.message,
            db=db
        )
        
        # Broadcast message to all connected clients
        await manager.broadcast(
            json.dumps({
                "type": "new_message",
                "data": result
            }),
            request_id
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/requests/{request_id}/messages")
async def get_messages(
    request_id: str,
    db: Session = Depends(get_db)
):
    """Get all messages for a support request"""
    try:
        messages = human_support_service.get_messages(request_id, db)
        return messages
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/{request_id}")
async def websocket_endpoint(websocket: WebSocket, request_id: str):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket, request_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle different message types
            if message_data.get("type") == "ping":
                await manager.send_personal_message(
                    json.dumps({"type": "pong"}), 
                    websocket
                )
            elif message_data.get("type") == "user_typing":
                # Broadcast typing indicator to other clients
                await manager.broadcast(
                    json.dumps({
                        "type": "user_typing",
                        "sender": message_data.get("sender", "user")
                    }),
                    request_id
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, request_id)