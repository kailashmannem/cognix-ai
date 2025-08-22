from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import logging

from models.chat import ChatResponse, MessageResponse, ChatSessionCreate, MessageCreateValidated
from models.user import User
from services.chat_service import chat_service
from utils.auth_middleware import get_current_user
from utils.database_router import db_router

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[ChatResponse])
async def get_chats(
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit number of chats returned"),
    current_user: User = Depends(get_current_user)
):
    """Get user's chat sessions"""
    try:
        # Check if user has database connection configured
        if not current_user.user_mongodb_connection:
            raise HTTPException(
                status_code=400,
                detail="User database connection not configured. Please set up your MongoDB connection in settings."
            )
        
        # Get user's chat sessions
        chats = await chat_service.get_user_chats(
            user_id=str(current_user.id),
            user_connection=current_user.user_mongodb_connection,
            limit=limit
        )
        
        # Convert to response models
        chat_responses = []
        for chat in chats:
            chat_responses.append(ChatResponse(
                id=str(chat.id),
                title=chat.title,
                document_name=chat.document_name,
                created_at=chat.created_at,
                updated_at=chat.updated_at
            ))
        
        return chat_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chats for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat sessions")


@router.post("/", response_model=ChatResponse)
async def create_chat(
    chat_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user)
):
    """Create new chat session"""
    try:
        # Check if user has database connection configured
        if not current_user.user_mongodb_connection:
            raise HTTPException(
                status_code=400,
                detail="User database connection not configured. Please set up your MongoDB connection in settings."
            )
        
        # Create chat session
        chat = await chat_service.create_chat_session(
            user_id=str(current_user.id),
            user_connection=current_user.user_mongodb_connection,
            title=chat_data.title
        )
        
        # Convert to response model
        return ChatResponse(
            id=str(chat.id),
            title=chat.title,
            document_name=chat.document_name,
            created_at=chat.created_at,
            updated_at=chat.updated_at
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create chat for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create chat session")


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get specific chat session"""
    try:
        # Check if user has database connection configured
        if not current_user.user_mongodb_connection:
            raise HTTPException(
                status_code=400,
                detail="User database connection not configured. Please set up your MongoDB connection in settings."
            )
        
        # Get chat session
        chat = await chat_service.get_chat_session(
            chat_id=chat_id,
            user_id=str(current_user.id),
            user_connection=current_user.user_mongodb_connection
        )
        
        if not chat:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        # Verify ownership
        if chat.user_id != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied to this chat session")
        
        # Convert to response model
        return ChatResponse(
            id=str(chat.id),
            title=chat.title,
            document_name=chat.document_name,
            created_at=chat.created_at,
            updated_at=chat.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat {chat_id} for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat session")


@router.get("/{chat_id}/messages", response_model=List[MessageResponse])
async def get_chat_messages(
    chat_id: str,
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of messages returned"),
    skip: Optional[int] = Query(None, ge=0, description="Number of messages to skip"),
    current_user: User = Depends(get_current_user)
):
    """Get messages for a specific chat session"""
    try:
        # Check if user has database connection configured
        if not current_user.user_mongodb_connection:
            raise HTTPException(
                status_code=400,
                detail="User database connection not configured. Please set up your MongoDB connection in settings."
            )
        
        # Get messages
        messages = await chat_service.get_chat_messages(
            chat_id=chat_id,
            user_id=str(current_user.id),
            user_connection=current_user.user_mongodb_connection,
            limit=limit,
            skip=skip
        )
        
        # Convert to response models
        message_responses = []
        for message in messages:
            message_responses.append(MessageResponse(
                id=str(message.id),
                content=message.content,
                role=message.role,
                timestamp=message.timestamp,
                context_used=message.context_used
            ))
        
        return message_responses
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get messages for chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve messages")


@router.post("/{chat_id}/messages", response_model=MessageResponse)
async def send_message(
    chat_id: str,
    message_data: MessageCreateValidated,
    current_user: User = Depends(get_current_user)
):
    """Send message to chat"""
    try:
        # Check if user has database connection configured
        if not current_user.user_mongodb_connection:
            raise HTTPException(
                status_code=400,
                detail="User database connection not configured. Please set up your MongoDB connection in settings."
            )
        
        # Send message
        message = await chat_service.send_message(
            chat_id=chat_id,
            user_id=str(current_user.id),
            user_connection=current_user.user_mongodb_connection,
            content=message_data.content,
            role=message_data.role
        )
        
        # Convert to response model
        return MessageResponse(
            id=str(message.id),
            content=message.content,
            role=message.role,
            timestamp=message.timestamp,
            context_used=message.context_used
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to send message to chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete chat session"""
    try:
        # Check if user has database connection configured
        if not current_user.user_mongodb_connection:
            raise HTTPException(
                status_code=400,
                detail="User database connection not configured. Please set up your MongoDB connection in settings."
            )
        
        # Delete chat session
        success = await chat_service.delete_chat_session(
            chat_id=chat_id,
            user_id=str(current_user.id),
            user_connection=current_user.user_mongodb_connection
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete chat session")
        
        return {"message": "Chat session deleted successfully"}
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete chat session")


@router.get("/{chat_id}/statistics")
async def get_chat_statistics(
    current_user: User = Depends(get_current_user)
):
    """Get statistics about user's chats"""
    try:
        # Check if user has database connection configured
        if not current_user.user_mongodb_connection:
            raise HTTPException(
                status_code=400,
                detail="User database connection not configured. Please set up your MongoDB connection in settings."
            )
        
        # Get chat statistics
        stats = await chat_service.get_chat_statistics(
            user_id=str(current_user.id),
            user_connection=current_user.user_mongodb_connection
        )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat statistics for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat statistics")