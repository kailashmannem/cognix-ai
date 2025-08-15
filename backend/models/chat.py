"""Chat and message models"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId

from models.user import PyObjectId


class ChatSession(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    title: str
    document_name: Optional[str] = None
    document_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Message(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    chat_id: str
    content: str
    role: str  # "user" or "assistant"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context_used: Optional[List[str]] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ChatCreate(BaseModel):
    title: str


class MessageCreate(BaseModel):
    content: str


class ChatResponse(BaseModel):
    id: str
    title: str
    document_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: str
    content: str
    role: str
    timestamp: datetime
    context_used: Optional[List[str]] = None

    model_config = {"from_attributes": True}


class ChatValidation:
    """Additional validation methods for Chat models"""
    
    @staticmethod
    def validate_chat_title(title: str) -> bool:
        """Validate chat title meets requirements"""
        if not title or len(title.strip()) == 0:
            return False
        if len(title) > 200:
            return False
        return True
    
    @staticmethod
    def validate_message_content(content: str) -> bool:
        """Validate message content"""
        if not content or len(content.strip()) == 0:
            return False
        if len(content) > 10000:  # 10KB limit
            return False
        return True
    
    @staticmethod
    def validate_message_role(role: str) -> bool:
        """Validate message role"""
        allowed_roles = ['user', 'assistant', 'system']
        return role in allowed_roles
    
    @staticmethod
    def sanitize_chat_data(chat_data: dict) -> dict:
        """Sanitize chat data before storage"""
        sanitized = chat_data.copy()
        
        if 'title' in sanitized:
            sanitized['title'] = sanitized['title'].strip()
        
        return sanitized
    
    @staticmethod
    def sanitize_message_content(content: str) -> str:
        """Sanitize message content"""
        # Remove potential harmful content while preserving formatting
        sanitized = content.strip()
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        return sanitized


# Enhanced models with validation
class ChatSessionCreate(BaseModel):
    title: str
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not ChatValidation.validate_chat_title(v):
            raise ValueError('Title must be between 1 and 200 characters')
        return v.strip()


class MessageCreateValidated(BaseModel):
    content: str
    role: str = "user"
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not ChatValidation.validate_message_content(v):
            raise ValueError('Message content must be between 1 and 10000 characters')
        return ChatValidation.sanitize_message_content(v)
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if not ChatValidation.validate_message_role(v):
            raise ValueError('Role must be one of: user, assistant, system')
        return v