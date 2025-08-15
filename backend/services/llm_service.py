"""LLM service for managing different AI providers"""

from abc import ABC, abstractmethod
from typing import List, Optional

from models.chat import Message


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def generate_response(self, messages: List[Message], context: str = None) -> str:
        """Generate response from LLM"""
        pass

    @abstractmethod
    async def validate_api_key(self, api_key: str) -> bool:
        """Validate API key for the provider"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation - to be implemented"""
    
    async def generate_response(self, messages: List[Message], context: str = None) -> str:
        pass

    async def validate_api_key(self, api_key: str) -> bool:
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini provider implementation - to be implemented"""
    
    async def generate_response(self, messages: List[Message], context: str = None) -> str:
        pass

    async def validate_api_key(self, api_key: str) -> bool:
        pass


class GroqProvider(LLMProvider):
    """Groq provider implementation - to be implemented"""
    
    async def generate_response(self, messages: List[Message], context: str = None) -> str:
        pass

    async def validate_api_key(self, api_key: str) -> bool:
        pass


class MistralProvider(LLMProvider):
    """Mistral provider implementation - to be implemented"""
    
    async def generate_response(self, messages: List[Message], context: str = None) -> str:
        pass

    async def validate_api_key(self, api_key: str) -> bool:
        pass


class OllamaProvider(LLMProvider):
    """Ollama local provider implementation - to be implemented"""
    
    async def generate_response(self, messages: List[Message], context: str = None) -> str:
        pass

    async def validate_api_key(self, api_key: str) -> bool:
        # Ollama doesn't require API key validation
        return True


class LLMService:
    """Main LLM service that manages different providers"""
    
    def __init__(self):
        self.providers = {
            "openai": OpenAIProvider(),
            "gemini": GeminiProvider(),
            "groq": GroqProvider(),
            "mistral": MistralProvider(),
            "ollama": OllamaProvider()
        }

    async def get_contextual_response(self, provider: str, chat_id: str, user_message: str, 
                                    user_api_key: str, context: str = None) -> str:
        """Get contextual response from specified LLM provider - to be implemented"""
        pass

    async def validate_api_key(self, provider: str, api_key: str) -> bool:
        """Validate API key for specified provider - to be implemented"""
        pass