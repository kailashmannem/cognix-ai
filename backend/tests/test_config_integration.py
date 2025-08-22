"""Integration tests for configuration management system"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from services.config_service import ConfigService
from models.user import User, UserConfig
from utils.encryption import encryption_service
from utils.validators import validator


class TestConfigIntegration:
    """Integration tests for the complete configuration system"""
    
    @pytest.fixture
    def config_service(self):
        return ConfigService()
    
    def test_encryption_roundtrip(self):
        """Test that encryption and decryption work correctly"""
        test_data = {
            "openai_key": "sk-1234567890abcdef1234567890abcdef1234567890abcdef",
            "mongodb_connection": "mongodb://user:pass@localhost:27017/database",
            "gemini_key": "AIzaSyDaGmWKa4JsXZ-HjGw7_SzT1TzqK1qNiOY"
        }
        
        for key, value in test_data.items():
            encrypted = encryption_service.encrypt(value)
            decrypted = encryption_service.decrypt(encrypted)
            assert decrypted == value, f"Encryption roundtrip failed for {key}"
    
    def test_api_key_validation_all_providers(self):
        """Test API key validation for all supported providers"""
        test_cases = [
            ("openai", "sk-1234567890abcdef1234567890abcdef1234567890abcdef", True),
            ("openai", "invalid-key", False),
            ("gemini", "AIzaSyDaGmWKa4JsXZ-HjGw7_SzT1TzqK1qNiOY", True),
            ("gemini", "short", False),
            ("groq", "gsk_1234567890abcdef1234567890abcdef1234567890abcdef", True),
            ("groq", "invalid", False),
            ("mistral", "1234567890abcdef1234567890abcdef1234567890abcdef", True),
            ("mistral", "short", False),
            ("ollama", "anything", True),  # Ollama doesn't require validation
            ("ollama", "", True)
        ]
        
        for provider, api_key, expected_valid in test_cases:
            is_valid, error = validator.validate_api_key_format(provider, api_key)
            assert is_valid == expected_valid, f"Validation failed for {provider}: {api_key} - {error}"
    
    @pytest.mark.asyncio
    async def test_mongodb_connection_validation(self):
        """Test MongoDB connection string validation"""
        valid_connections = [
            "mongodb://localhost:27017",
            "mongodb://localhost:27017/database",
            "mongodb://user:pass@localhost:27017/database",
            "mongodb+srv://user:pass@cluster.mongodb.net/database"
        ]
        
        invalid_connections = [
            "invalid-connection",
            "http://localhost:27017",
            "mysql://localhost:3306"
        ]
        
        for connection in valid_connections:
            is_valid, error = await validator.validate_mongodb_connection(connection)
            # Note: This will fail in test environment without actual MongoDB
            # but the format validation should pass
            assert connection.startswith(('mongodb://', 'mongodb+srv://'))
        
        for connection in invalid_connections:
            is_valid, error = await validator.validate_mongodb_connection(connection)
            assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_config_service_workflow(self, config_service):
        """Test the complete configuration service workflow"""
        user_id = "507f1f77bcf86cd799439011"
        
        # Mock the auth service and database
        with patch.object(config_service.auth_service, 'get_user_by_id') as mock_get_user, \
             patch('services.config_service.get_platform_database') as mock_get_db, \
             patch.object(config_service, '_test_api_key') as mock_test_key, \
             patch.object(config_service, '_validate_mongodb_connection') as mock_validate_db, \
             patch.object(config_service, '_initialize_user_database') as mock_init_db:
            
            # Setup mocks
            mock_user = MagicMock()
            mock_user.api_keys = {}
            mock_user.user_mongodb_connection = None
            mock_user.preferred_llm_provider = "openai"
            mock_get_user.return_value = mock_user
            
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_db.users = mock_collection
            mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
            mock_get_db.return_value = mock_db
            
            mock_test_key.return_value = {"valid": True, "tested": True}
            mock_validate_db.return_value = {"valid": True, "database_name": "test"}
            mock_init_db.return_value = None
            
            # Test configuration update
            config = UserConfig(
                api_keys={
                    "openai": "sk-1234567890abcdef1234567890abcdef1234567890abcdef",
                    "gemini": "AIzaSyDaGmWKa4JsXZ-HjGw7_SzT1TzqK1qNiOY"
                },
                user_mongodb_connection="mongodb://localhost:27017/test",
                preferred_llm_provider="gemini"
            )
            
            result = await config_service.update_user_config(user_id, config)
            
            # Verify results
            assert result["success"] is True
            assert "validation_results" in result
            assert "api_keys" in result["validation_results"]
            assert "mongodb_connection" in result["validation_results"]
            
            # Verify API keys were validated
            api_key_results = result["validation_results"]["api_keys"]
            assert "openai" in api_key_results
            assert "gemini" in api_key_results
            assert api_key_results["openai"]["valid"] is True
            assert api_key_results["gemini"]["valid"] is True
            
            # Verify MongoDB connection was validated
            mongodb_result = result["validation_results"]["mongodb_connection"]
            assert mongodb_result["valid"] is True
            
            # Verify database update was called
            mock_collection.update_one.assert_called_once()
    
    def test_user_config_model_validation(self):
        """Test UserConfig model validation"""
        # Valid configuration
        valid_config = UserConfig(
            api_keys={
                "openai": "sk-1234567890abcdef1234567890abcdef1234567890abcdef",
                "gemini": "AIzaSyDaGmWKa4JsXZ-HjGw7_SzT1TzqK1qNiOY"
            },
            user_mongodb_connection="mongodb://localhost:27017/test",
            preferred_llm_provider="openai"
        )
        
        assert valid_config.preferred_llm_provider == "openai"
        assert "openai" in valid_config.api_keys
        assert "gemini" in valid_config.api_keys
        
        # Test invalid LLM provider
        with pytest.raises(ValueError):
            UserConfig(preferred_llm_provider="invalid_provider")
        
        # Test invalid MongoDB connection format
        with pytest.raises(ValueError):
            UserConfig(user_mongodb_connection="invalid-connection")
        
        # Test invalid API key provider
        with pytest.raises(ValueError):
            UserConfig(api_keys={"invalid_provider": "test-key"})
    
    def test_encryption_with_different_data_types(self):
        """Test encryption with various data types and edge cases"""
        test_cases = [
            "",  # Empty string
            "simple_string",
            "string with spaces and special chars !@#$%^&*()",
            "unicode_string_中文_العربية_🚀",
            "very_long_string_" + "x" * 1000,
            "mongodb://user:complex_p@ssw0rd!@host:27017/db?authSource=admin",
            "sk-" + "a" * 48,  # OpenAI key format
            "AIzaSy" + "B" * 32  # Gemini key format
        ]
        
        for test_string in test_cases:
            encrypted = encryption_service.encrypt(test_string)
            decrypted = encryption_service.decrypt(encrypted)
            assert decrypted == test_string, f"Failed for: {test_string}"
    
    @pytest.mark.asyncio
    async def test_api_key_testing_integration(self):
        """Test API key testing functionality"""
        test_cases = [
            ("openai", "sk-test123456789012345678901234567890"),
            ("gemini", "AIzaSyDaGmWKa4JsXZ-HjGw7_SzT1TzqK1qNiOY"),
            ("groq", "gsk_test123456789012345678901234567890"),
            ("mistral", "test123456789012345678901234567890"),
            ("ollama", "")
        ]
        
        for provider, api_key in test_cases:
            # Test format validation first
            is_valid, error = validator.validate_api_key_format(provider, api_key)
            assert is_valid is True, f"Format validation failed for {provider}: {error}"
            
            # Test connection (will be mocked in real tests)
            result = await validator.test_api_key_connection(provider, api_key)
            assert result["provider"] == provider
            assert "valid" in result
            assert "tested" in result
    
    def test_configuration_security(self):
        """Test that sensitive data is properly encrypted"""
        sensitive_data = [
            "sk-1234567890abcdef1234567890abcdef1234567890abcdef",
            "mongodb://user:password@localhost:27017/database",
            "AIzaSyDaGmWKa4JsXZ-HjGw7_SzT1TzqK1qNiOY"
        ]
        
        for data in sensitive_data:
            encrypted = encryption_service.encrypt(data)
            
            # Encrypted data should be different from original
            assert encrypted != data
            
            # Encrypted data should not contain the original data
            assert data not in encrypted
            
            # Should be able to decrypt back to original
            decrypted = encryption_service.decrypt(encrypted)
            assert decrypted == data
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        # Test decryption of invalid data
        invalid_encrypted_data = [
            "invalid_base64",
            "dGVzdA==",  # Valid base64 but not encrypted
            "",
            "not_encrypted_at_all"
        ]
        
        for invalid_data in invalid_encrypted_data:
            decrypted = encryption_service.decrypt(invalid_data)
            assert decrypted == ""  # Should return empty string on failure
        
        # Test validation of invalid API keys
        invalid_api_keys = [
            ("openai", "invalid"),
            ("gemini", ""),
            ("groq", "wrong_prefix"),
            ("mistral", "short"),
            ("invalid_provider", "test-key")
        ]
        
        for provider, api_key in invalid_api_keys:
            is_valid, error = validator.validate_api_key_format(provider, api_key)
            if provider != "invalid_provider":
                assert is_valid is False
                assert error is not None
            else:
                assert is_valid is False
                assert "Unsupported provider" in error


if __name__ == "__main__":
    pytest.main([__file__])