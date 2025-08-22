"""Tests for validation utilities"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from utils.validators import ValidationService, validator


class TestValidationService:
    """Test cases for ValidationService"""
    
    def test_validate_email_valid(self):
        """Test valid email validation"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@example.com"
        ]
        
        for email in valid_emails:
            assert validator.validate_email(email) is True
    
    def test_validate_email_invalid(self):
        """Test invalid email validation"""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test..test@example.com",
            "test@example",
            ""
        ]
        
        for email in invalid_emails:
            assert validator.validate_email(email) is False
    
    def test_validate_password_strong(self):
        """Test strong password validation"""
        strong_passwords = [
            "Password123",
            "MyStr0ngP@ss",
            "Test1234",
            "ComplexPass1"
        ]
        
        for password in strong_passwords:
            is_valid, errors = validator.validate_password(password)
            assert is_valid is True
            assert len(errors) == 0
    
    def test_validate_password_weak(self):
        """Test weak password validation"""
        weak_passwords = [
            ("short", ["Password must be at least 8 characters long"]),
            ("lowercase", ["Password must contain at least one uppercase letter", 
                         "Password must contain at least one digit"]),
            ("UPPERCASE", ["Password must contain at least one lowercase letter", 
                         "Password must contain at least one digit"]),
            ("NoNumbers", ["Password must contain at least one digit"]),
            ("nonumbers", ["Password must contain at least one uppercase letter", 
                         "Password must contain at least one digit"])
        ]
        
        for password, expected_errors in weak_passwords:
            is_valid, errors = validator.validate_password(password)
            assert is_valid is False
            for expected_error in expected_errors:
                assert expected_error in errors
    
    def test_validate_llm_provider_valid(self):
        """Test valid LLM provider validation"""
        valid_providers = ["openai", "gemini", "groq", "mistral", "ollama"]
        
        for provider in valid_providers:
            assert validator.validate_llm_provider(provider) is True
            assert validator.validate_llm_provider(provider.upper()) is True
    
    def test_validate_llm_provider_invalid(self):
        """Test invalid LLM provider validation"""
        invalid_providers = ["invalid", "gpt", "claude", ""]
        
        for provider in invalid_providers:
            assert validator.validate_llm_provider(provider) is False
    
    def test_validate_api_key_format_openai_valid(self):
        """Test valid OpenAI API key format"""
        valid_keys = [
            "sk-1234567890123456789012345678901234567890123456789012",
            "sk-abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOP"
        ]
        
        for key in valid_keys:
            is_valid, error = validator.validate_api_key_format("openai", key)
            assert is_valid is True
            assert error is None
    
    def test_validate_api_key_format_openai_invalid(self):
        """Test invalid OpenAI API key format"""
        invalid_keys = [
            ("", "API key cannot be empty"),
            ("invalid", "OpenAI API key must start with 'sk-'"),
            ("sk-short", "OpenAI API key is too short"),
            ("sk-" + "x" * 200, "OpenAI API key is too long")
        ]
        
        for key, expected_error in invalid_keys:
            is_valid, error = validator.validate_api_key_format("openai", key)
            assert is_valid is False
            assert expected_error in error
    
    def test_validate_api_key_format_gemini_valid(self):
        """Test valid Gemini API key format"""
        valid_keys = [
            "AIzaSyDaGmWKa4JsXZ-HjGw7_SzT1TzqK1qNiOY",
            "test-gemini-key-123456789012345678901234567890"
        ]
        
        for key in valid_keys:
            is_valid, error = validator.validate_api_key_format("gemini", key)
            assert is_valid is True
            assert error is None
    
    def test_validate_api_key_format_gemini_invalid(self):
        """Test invalid Gemini API key format"""
        invalid_keys = [
            ("", "API key cannot be empty"),
            ("short", "Gemini API key is too short"),
            ("x" * 200, "Gemini API key is too long"),
            ("invalid@key!", "Gemini API key contains invalid characters")
        ]
        
        for key, expected_error in invalid_keys:
            is_valid, error = validator.validate_api_key_format("gemini", key)
            assert is_valid is False
            assert expected_error in error
    
    def test_validate_api_key_format_groq_valid(self):
        """Test valid Groq API key format"""
        valid_keys = [
            "gsk_1234567890123456789012345678901234567890123456789012",
            "gsk_abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOP"
        ]
        
        for key in valid_keys:
            is_valid, error = validator.validate_api_key_format("groq", key)
            assert is_valid is True
            assert error is None
    
    def test_validate_api_key_format_groq_invalid(self):
        """Test invalid Groq API key format"""
        invalid_keys = [
            ("", "API key cannot be empty"),
            ("invalid", "Groq API key must start with 'gsk_'"),
            ("gsk_short", "Groq API key is too short"),
            ("gsk_" + "x" * 200, "Groq API key is too long")
        ]
        
        for key, expected_error in invalid_keys:
            is_valid, error = validator.validate_api_key_format("groq", key)
            assert is_valid is False
            assert expected_error in error
    
    def test_validate_api_key_format_mistral_valid(self):
        """Test valid Mistral API key format"""
        valid_keys = [
            "1234567890123456789012345678901234567890123456789012",
            "abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOP"
        ]
        
        for key in valid_keys:
            is_valid, error = validator.validate_api_key_format("mistral", key)
            assert is_valid is True
            assert error is None
    
    def test_validate_api_key_format_mistral_invalid(self):
        """Test invalid Mistral API key format"""
        invalid_keys = [
            ("", "API key cannot be empty"),
            ("short", "Mistral API key is too short"),
            ("x" * 200, "Mistral API key is too long"),
            ("invalid@key!", "Mistral API key contains invalid characters")
        ]
        
        for key, expected_error in invalid_keys:
            is_valid, error = validator.validate_api_key_format("mistral", key)
            assert is_valid is False
            assert expected_error in error
    
    def test_validate_api_key_format_ollama(self):
        """Test Ollama API key format (should always be valid)"""
        test_keys = ["", "anything", "123", "invalid@key!"]
        
        for key in test_keys:
            is_valid, error = validator.validate_api_key_format("ollama", key)
            assert is_valid is True
            assert error is None
    
    def test_validate_api_key_format_unsupported_provider(self):
        """Test unsupported provider"""
        is_valid, error = validator.validate_api_key_format("unsupported", "test-key")
        assert is_valid is False
        assert "Unsupported provider" in error
    
    @pytest.mark.asyncio
    async def test_validate_mongodb_connection_valid(self):
        """Test valid MongoDB connection validation"""
        connection_string = "mongodb://localhost:27017/test"
        
        with patch('motor.motor_asyncio.AsyncIOMotorClient') as mock_client:
            mock_instance = MagicMock()
            mock_instance.admin.command = AsyncMock()
            mock_instance.close = MagicMock()
            mock_client.return_value = mock_instance
            
            is_valid, error = await validator.validate_mongodb_connection(connection_string)
            
            assert is_valid is True
            assert error is None
            mock_client.assert_called_once_with(connection_string, serverSelectionTimeoutMS=5000)
            mock_instance.admin.command.assert_called_once_with('ping')
    
    @pytest.mark.asyncio
    async def test_validate_mongodb_connection_invalid_format(self):
        """Test invalid MongoDB connection format"""
        invalid_connections = [
            "invalid-connection",
            "http://localhost:27017",
            "mysql://localhost:3306"
        ]
        
        for connection in invalid_connections:
            is_valid, error = await validator.validate_mongodb_connection(connection)
            assert is_valid is False
            assert "Invalid MongoDB connection string format" in error
    
    @pytest.mark.asyncio
    async def test_validate_mongodb_connection_failure(self):
        """Test MongoDB connection failure"""
        connection_string = "mongodb://invalid:27017/test"
        
        with patch('motor.motor_asyncio.AsyncIOMotorClient') as mock_client:
            mock_instance = MagicMock()
            mock_instance.admin.command = AsyncMock(side_effect=Exception("Connection failed"))
            mock_instance.close = MagicMock()
            mock_client.return_value = mock_instance
            
            is_valid, error = await validator.validate_mongodb_connection(connection_string)
            
            assert is_valid is False
            assert "Connection failed" in error
    
    @pytest.mark.asyncio
    async def test_test_api_key_connection_openai_success(self):
        """Test OpenAI API key connection testing"""
        provider = "openai"
        api_key = "sk-test123456789012345678901234567890"
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_models = MagicMock()
            mock_models_data = MagicMock()
            mock_models_data.data = ["model1", "model2"]
            mock_models.list = AsyncMock(return_value=mock_models_data)
            mock_client.models = mock_models
            mock_openai.return_value = mock_client
            
            result = await validator.test_api_key_connection(provider, api_key)
            
            assert result["provider"] == provider
            assert result["valid"] is True
            assert result["tested"] is True
            assert result["model_count"] == 2
            assert result["response_time"] is not None
    
    @pytest.mark.asyncio
    async def test_test_api_key_connection_openai_failure(self):
        """Test OpenAI API key connection testing failure"""
        provider = "openai"
        api_key = "sk-invalid123456789012345678901234567890"
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_models = MagicMock()
            mock_models.list = AsyncMock(side_effect=Exception("Invalid API key"))
            mock_client.models = mock_models
            mock_openai.return_value = mock_client
            
            result = await validator.test_api_key_connection(provider, api_key)
            
            assert result["provider"] == provider
            assert result["valid"] is False
            assert result["tested"] is True
            assert "Invalid API key" in result["error"]
    
    @pytest.mark.asyncio
    async def test_test_api_key_connection_ollama_success(self):
        """Test Ollama API key connection testing"""
        provider = "ollama"
        api_key = ""  # Ollama doesn't need API key
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            result = await validator.test_api_key_connection(provider, api_key)
            
            assert result["provider"] == provider
            assert result["valid"] is True
            assert result["tested"] is True
            assert "Ollama local server is accessible" in result["note"]
    
    @pytest.mark.asyncio
    async def test_test_api_key_connection_ollama_failure(self):
        """Test Ollama API key connection testing failure"""
        provider = "ollama"
        api_key = ""
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = MagicMock()
            mock_response.status = 404
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            result = await validator.test_api_key_connection(provider, api_key)
            
            assert result["provider"] == provider
            assert result["valid"] is False
            assert result["tested"] is True
            assert "Ollama server returned status 404" in result["error"]
    
    @pytest.mark.asyncio
    async def test_test_api_key_connection_unsupported_provider(self):
        """Test API key connection testing for unsupported provider"""
        provider = "unsupported"
        api_key = "test-key"
        
        result = await validator.test_api_key_connection(provider, api_key)
        
        assert result["provider"] == provider
        assert result["valid"] is False
        assert "Unsupported provider" in result["error"]
    
    def test_validate_file_type_valid(self):
        """Test valid file type validation"""
        # Assuming ALLOWED_EXTENSIONS is "pdf,docx,txt"
        with patch('utils.validators.settings') as mock_settings:
            mock_settings.ALLOWED_EXTENSIONS = "pdf,docx,txt"
            
            valid_files = [
                "document.pdf",
                "report.docx",
                "notes.txt",
                "FILE.PDF",  # Case insensitive
                "data.TXT"
            ]
            
            for filename in valid_files:
                assert validator.validate_file_type(filename) is True
    
    def test_validate_file_type_invalid(self):
        """Test invalid file type validation"""
        with patch('utils.validators.settings') as mock_settings:
            mock_settings.ALLOWED_EXTENSIONS = "pdf,docx,txt"
            
            invalid_files = [
                "image.jpg",
                "video.mp4",
                "archive.zip",
                "script.py",
                "document"  # No extension
            ]
            
            for filename in invalid_files:
                assert validator.validate_file_type(filename) is False
    
    def test_validate_file_size_valid(self):
        """Test valid file size validation"""
        with patch('utils.validators.settings') as mock_settings:
            mock_settings.MAX_FILE_SIZE = 10485760  # 10MB
            
            valid_sizes = [1024, 1048576, 5242880, 10485760]  # 1KB, 1MB, 5MB, 10MB
            
            for size in valid_sizes:
                assert validator.validate_file_size(size) is True
    
    def test_validate_file_size_invalid(self):
        """Test invalid file size validation"""
        with patch('utils.validators.settings') as mock_settings:
            mock_settings.MAX_FILE_SIZE = 10485760  # 10MB
            
            invalid_sizes = [10485761, 20971520, 52428800]  # 10MB+1, 20MB, 50MB
            
            for size in invalid_sizes:
                assert validator.validate_file_size(size) is False


if __name__ == "__main__":
    pytest.main([__file__])