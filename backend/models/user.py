"""User model for authentication and configuration"""

from typing import Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId
import re


class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema, handler):
        field_schema.update(type="string", format="objectid")
        return field_schema


class User(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    email: str
    password_hash: str
    api_keys: Optional[Dict[str, str]] = Field(default_factory=dict)
    user_mongodb_connection: Optional[str] = None
    preferred_llm_provider: str = "openai"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class UserCreate(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    preferred_llm_provider: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserConfig(BaseModel):
    api_keys: Optional[Dict[str, str]] = None
    user_mongodb_connection: Optional[str] = None
    preferred_llm_provider: Optional[str] = None
    
    @field_validator('preferred_llm_provider')
    @classmethod
    def validate_llm_provider(cls, v):
        if v is not None:
            allowed_providers = ['openai', 'gemini', 'groq', 'mistral', 'ollama']
            if v not in allowed_providers:
                raise ValueError(f'LLM provider must be one of: {allowed_providers}')
        return v
    
    @field_validator('user_mongodb_connection')
    @classmethod
    def validate_mongodb_connection(cls, v):
        if v is not None:
            # Basic MongoDB connection string validation
            if not v.startswith(('mongodb://', 'mongodb+srv://')):
                raise ValueError('MongoDB connection string must start with mongodb:// or mongodb+srv://')
        return v
    
    @field_validator('api_keys')
    @classmethod
    def validate_api_keys(cls, v):
        if v is not None:
            allowed_providers = ['openai', 'gemini', 'groq', 'mistral']
            for provider in v.keys():
                if provider not in allowed_providers:
                    raise ValueError(f'API key provider must be one of: {allowed_providers}')
        return v


class UserValidation:
    """Additional validation methods for User model"""
    
    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """Validate password meets security requirements"""
        if len(password) < 8:
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'\d', password):
            return False
        return True
    
    @staticmethod
    def validate_email_format(email: str) -> bool:
        """Additional email validation beyond Pydantic"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    @staticmethod
    def sanitize_user_data(user_data: Dict) -> Dict:
        """Sanitize user data before storage"""
        sanitized = user_data.copy()
        
        # Remove any potential script tags or HTML
        if 'email' in sanitized:
            sanitized['email'] = sanitized['email'].strip().lower()
        
        return sanitized