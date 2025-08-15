"""Validation utilities for various data types"""

import re
from typing import List, Optional
from urllib.parse import urlparse
import pymongo
from motor.motor_asyncio import AsyncIOMotorClient

from utils.config import settings


class ValidationService:
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_file_type(filename: str) -> bool:
        """Validate if file type is allowed"""
        allowed_extensions = settings.ALLOWED_EXTENSIONS.split(',')
        file_extension = filename.lower().split('.')[-1]
        return file_extension in allowed_extensions
    
    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        """Validate if file size is within limits"""
        return file_size <= settings.MAX_FILE_SIZE
    
    @staticmethod
    async def validate_mongodb_connection(connection_string: str) -> tuple[bool, Optional[str]]:
        """Validate MongoDB connection string"""
        try:
            # Parse the connection string
            parsed = urlparse(connection_string)
            if not parsed.scheme.startswith('mongodb'):
                return False, "Invalid MongoDB connection string format"
            
            # Test the connection
            client = AsyncIOMotorClient(connection_string, serverSelectionTimeoutMS=5000)
            await client.admin.command('ping')
            client.close()
            
            return True, None
            
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    @staticmethod
    def validate_llm_provider(provider: str) -> bool:
        """Validate if LLM provider is supported"""
        supported_providers = ['openai', 'gemini', 'groq', 'mistral', 'ollama']
        return provider.lower() in supported_providers
    
    @staticmethod
    def validate_api_key_format(provider: str, api_key: str) -> tuple[bool, Optional[str]]:
        """Validate API key format for different providers"""
        if not api_key:
            return False, "API key cannot be empty"
        
        provider = provider.lower()
        
        if provider == 'openai':
            if not api_key.startswith('sk-'):
                return False, "OpenAI API key must start with 'sk-'"
            if len(api_key) < 20:
                return False, "OpenAI API key is too short"
        
        elif provider == 'gemini':
            if len(api_key) < 20:
                return False, "Gemini API key is too short"
        
        elif provider == 'groq':
            if not api_key.startswith('gsk_'):
                return False, "Groq API key must start with 'gsk_'"
        
        elif provider == 'mistral':
            if len(api_key) < 20:
                return False, "Mistral API key is too short"
        
        elif provider == 'ollama':
            # Ollama doesn't require API key validation
            return True, None
        
        return True, None


# Global validation service instance
validator = ValidationService()