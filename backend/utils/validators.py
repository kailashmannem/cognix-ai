"""Validation utilities for various data types"""

import re
from typing import List, Optional, Dict, Any
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
        provider = provider.lower()
        
        # Ollama doesn't require API key validation (local deployment)
        if provider == 'ollama':
            return True, None
        
        if not api_key:
            return False, "API key cannot be empty"
        
        if provider == 'openai':
            if not api_key.startswith('sk-'):
                return False, "OpenAI API key must start with 'sk-'"
            if len(api_key) < 20:
                return False, "OpenAI API key is too short"
            # OpenAI keys are typically 51 characters long
            if len(api_key) > 100:
                return False, "OpenAI API key is too long"
        
        elif provider == 'gemini':
            if len(api_key) < 20:
                return False, "Gemini API key is too short"
            if len(api_key) > 100:
                return False, "Gemini API key is too long"
            # Gemini keys typically contain alphanumeric characters and hyphens
            if not re.match(r'^[A-Za-z0-9_-]+$', api_key):
                return False, "Gemini API key contains invalid characters"
        
        elif provider == 'groq':
            if not api_key.startswith('gsk_'):
                return False, "Groq API key must start with 'gsk_'"
            if len(api_key) < 20:
                return False, "Groq API key is too short"
            if len(api_key) > 100:
                return False, "Groq API key is too long"
        
        elif provider == 'mistral':
            if len(api_key) < 20:
                return False, "Mistral API key is too short"
            if len(api_key) > 100:
                return False, "Mistral API key is too long"
            # Mistral keys typically contain alphanumeric characters
            if not re.match(r'^[A-Za-z0-9_-]+$', api_key):
                return False, "Mistral API key contains invalid characters"
        
        else:
            return False, f"Unsupported provider: {provider}"
        
        return True, None
    
    @staticmethod
    async def test_api_key_connection(provider: str, api_key: str) -> Dict[str, Any]:
        """Test API key by making a simple API call to the provider"""
        result = {
            "provider": provider,
            "valid": False,
            "tested": False,
            "error": None,
            "response_time": None
        }
        
        import time
        start_time = time.time()
        
        try:
            if provider == "openai":
                import openai
                client = openai.AsyncOpenAI(api_key=api_key)
                # Test with a simple models list call
                models = await client.models.list()
                result["valid"] = True
                result["tested"] = True
                result["model_count"] = len(models.data) if hasattr(models, 'data') else 0
                
            elif provider == "gemini":
                # Placeholder for Gemini API testing
                # In a real implementation, you'd use the Google AI SDK
                result["tested"] = False
                result["valid"] = True  # Assume valid if format is correct
                result["note"] = "Gemini API testing not implemented - format validation only"
                
            elif provider == "groq":
                # Placeholder for Groq API testing
                # In a real implementation, you'd use the Groq SDK
                result["tested"] = False
                result["valid"] = True  # Assume valid if format is correct
                result["note"] = "Groq API testing not implemented - format validation only"
                
            elif provider == "mistral":
                # Placeholder for Mistral API testing
                # In a real implementation, you'd use the Mistral SDK
                result["tested"] = False
                result["valid"] = True  # Assume valid if format is correct
                result["note"] = "Mistral API testing not implemented - format validation only"
                
            elif provider == "ollama":
                # For Ollama, we could test the local endpoint
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://localhost:11434/api/tags") as response:
                        if response.status == 200:
                            result["valid"] = True
                            result["tested"] = True
                            result["note"] = "Ollama local server is accessible"
                        else:
                            result["valid"] = False
                            result["error"] = f"Ollama server returned status {response.status}"
            
            else:
                result["error"] = f"Unsupported provider: {provider}"
                
        except Exception as e:
            result["valid"] = False
            result["error"] = str(e)
            result["tested"] = True  # We attempted to test
        
        result["response_time"] = round(time.time() - start_time, 3)
        return result


# Global validation service instance
validator = ValidationService()