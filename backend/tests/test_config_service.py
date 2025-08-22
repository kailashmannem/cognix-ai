"""Tests for configuration service"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from services.config_service import ConfigService
from models.user import User, UserConfig
from utils.encryption import encryption_service
from fastapi import HTTPException


class TestConfigService:
    """Test cases for ConfigService"""
    
    @pytest.fixture
    def config_service(self):
        return ConfigService()
    
    @pytest.fixture
    def sample_user(self):
        return User(
            id="507f1f77bcf86cd799439011",
            email="test@example.com",
            password_hash="hashed_password",
            api_keys={
                "openai": encryption_service.encrypt("sk-test123456789012345678901234567890"),
                "gemini": encryption_service.encrypt("test-gemini-key-123456789")
            },
            user_mongodb_connection=encryption_service.encrypt("mongodb://localhost:27017/test"),
            preferred_llm_provider="openai",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def sample_config(self):
        return UserConfig(
            api_keys={
                "openai": "sk-new123456789012345678901234567890",
                "groq": "gsk_test123456789012345678901234567890"
            },
            user_mongodb_connection="mongodb://localhost:27017/newtest",
            preferred_llm_provider="groq"
        )
    
    @pytest.mark.asyncio
    async def test_update_user_config_success(self, config_service, sample_config):
        """Test successful user configuration update"""
        user_id = "507f1f77bcf86cd799439011"
        
        with patch.object(config_service.auth_service, 'get_user_by_id') as mock_get_user, \
             patch('services.config_service.get_platform_database') as mock_get_db, \
             patch.object(config_service, '_test_api_key') as mock_test_key, \
             patch.object(config_service, '_validate_mongodb_connection') as mock_validate_db, \
             patch.object(config_service, '_initialize_user_database') as mock_init_db:
            
            # Setup mocks
            mock_user = MagicMock()
            mock_user.api_keys = {}
            mock_get_user.return_value = mock_user
            
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_db.users = mock_collection
            mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
            mock_get_db.return_value = mock_db
            
            mock_test_key.return_value = {"valid": True}
            mock_validate_db.return_value = {"valid": True, "database_name": "newtest"}
            mock_init_db.return_value = None
            
            # Execute
            result = await config_service.update_user_config(user_id, sample_config)
            
            # Verify
            assert result["success"] is True
            assert "validation_results" in result
            assert "api_keys" in result["validation_results"]
            assert "mongodb_connection" in result["validation_results"]
            mock_collection.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_user_config_invalid_api_key(self, config_service):
        """Test configuration update with invalid API key"""
        user_id = "507f1f77bcf86cd799439011"
        config = UserConfig(api_keys={"openai": "invalid-key"})
        
        with patch.object(config_service.auth_service, 'get_user_by_id') as mock_get_user, \
             patch('services.config_service.get_platform_database') as mock_get_db:
            
            mock_user = MagicMock()
            mock_user.api_keys = {}
            mock_get_user.return_value = mock_user
            
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_db.users = mock_collection
            mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
            mock_get_db.return_value = mock_db
            
            # Execute
            result = await config_service.update_user_config(user_id, config)
            
            # Verify
            assert result["success"] is True
            assert result["validation_results"]["api_keys"]["openai"]["valid"] is False
    
    @pytest.mark.asyncio
    async def test_get_user_config(self, config_service, sample_user):
        """Test getting user configuration"""
        user_id = str(sample_user.id)
        
        with patch.object(config_service.auth_service, 'get_user_by_id') as mock_get_user, \
             patch.object(config_service, '_validate_mongodb_connection') as mock_validate_db:
            
            mock_get_user.return_value = sample_user
            mock_validate_db.return_value = {"valid": True, "database_name": "test"}
            
            # Execute
            result = await config_service.get_user_config(user_id)
            
            # Verify
            assert "api_keys" in result
            assert "mongodb_connection" in result
            assert "preferred_llm_provider" in result
            assert result["preferred_llm_provider"] == "openai"
            assert result["api_keys"]["openai"]["configured"] is True
            assert result["mongodb_connection"]["configured"] is True
    
    @pytest.mark.asyncio
    async def test_get_user_api_key(self, config_service, sample_user):
        """Test getting decrypted API key"""
        user_id = str(sample_user.id)
        
        with patch.object(config_service.auth_service, 'get_user_by_id') as mock_get_user:
            mock_get_user.return_value = sample_user
            
            # Execute
            api_key = await config_service.get_user_api_key(user_id, "openai")
            
            # Verify
            assert api_key == "sk-test123456789012345678901234567890"
    
    @pytest.mark.asyncio
    async def test_get_user_mongodb_connection(self, config_service, sample_user):
        """Test getting decrypted MongoDB connection"""
        user_id = str(sample_user.id)
        
        with patch.object(config_service.auth_service, 'get_user_by_id') as mock_get_user:
            mock_get_user.return_value = sample_user
            
            # Execute
            connection = await config_service.get_user_mongodb_connection(user_id)
            
            # Verify
            assert connection == "mongodb://localhost:27017/test"
    
    @pytest.mark.asyncio
    async def test_delete_api_key(self, config_service):
        """Test deleting API key"""
        user_id = "507f1f77bcf86cd799439011"
        provider = "openai"
        
        with patch('services.config_service.get_platform_database') as mock_get_db:
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_db.users = mock_collection
            mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
            mock_get_db.return_value = mock_db
            
            # Execute
            result = await config_service.delete_api_key(user_id, provider)
            
            # Verify
            assert result is True
            mock_collection.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_test_api_key_openai_success(self, config_service):
        """Test OpenAI API key testing"""
        provider = "openai"
        api_key = "sk-test123456789012345678901234567890"
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_models = MagicMock()
            mock_models.list = AsyncMock()
            mock_client.models = mock_models
            mock_openai.return_value = mock_client
            
            # Execute
            result = await config_service._test_api_key(provider, api_key)
            
            # Verify
            assert result["valid"] is True
            assert result["tested"] is True
    
    @pytest.mark.asyncio
    async def test_test_api_key_openai_failure(self, config_service):
        """Test OpenAI API key testing with failure"""
        provider = "openai"
        api_key = "sk-invalid123456789012345678901234567890"
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_models = MagicMock()
            mock_models.list = AsyncMock(side_effect=Exception("Invalid API key"))
            mock_client.models = mock_models
            mock_openai.return_value = mock_client
            
            # Execute
            result = await config_service._test_api_key(provider, api_key)
            
            # Verify
            assert result["valid"] is False
            assert "Invalid API key" in result["error"]
    
    @pytest.mark.asyncio
    async def test_validate_mongodb_connection_success(self, config_service):
        """Test MongoDB connection validation success"""
        user_id = "507f1f77bcf86cd799439011"
        connection_string = "mongodb://localhost:27017/test"
        
        with patch('services.config_service.db_manager') as mock_db_manager:
            mock_db_manager.validate_user_connection.return_value = {
                "valid": True,
                "database_name": "test"
            }
            mock_db_manager.test_user_database_operations.return_value = {
                "success": True,
                "operations_tested": ["insert", "find", "update", "delete"]
            }
            
            # Execute
            result = await config_service._validate_mongodb_connection(user_id, connection_string)
            
            # Verify
            assert result["valid"] is True
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_validate_mongodb_connection_failure(self, config_service):
        """Test MongoDB connection validation failure"""
        user_id = "507f1f77bcf86cd799439011"
        connection_string = "mongodb://invalid:27017/test"
        
        with patch('services.config_service.db_manager') as mock_db_manager:
            mock_db_manager.validate_user_connection.return_value = {
                "valid": False,
                "error": "Connection failed"
            }
            
            # Execute
            result = await config_service._validate_mongodb_connection(user_id, connection_string)
            
            # Verify
            assert result["valid"] is False
            assert "Connection failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_initialize_user_database(self, config_service):
        """Test user database initialization"""
        user_id = "507f1f77bcf86cd799439011"
        connection_string = "mongodb://localhost:27017/test"
        
        with patch('services.config_service.db_manager') as mock_db_manager:
            mock_db_manager.get_user_database = AsyncMock()
            
            # Execute
            await config_service._initialize_user_database(user_id, connection_string)
            
            # Verify
            mock_db_manager.get_user_database.assert_called_once_with(user_id, connection_string)
    
    @pytest.mark.asyncio
    async def test_validate_all_user_configs(self, config_service, sample_user):
        """Test validating all user configurations"""
        user_id = str(sample_user.id)
        
        with patch.object(config_service.auth_service, 'get_user_by_id') as mock_get_user, \
             patch.object(config_service, '_test_api_key') as mock_test_key, \
             patch.object(config_service, '_validate_mongodb_connection') as mock_validate_db:
            
            mock_get_user.return_value = sample_user
            mock_test_key.return_value = {"valid": True}
            mock_validate_db.return_value = {"valid": True}
            
            # Execute
            result = await config_service.validate_all_user_configs(user_id)
            
            # Verify
            assert result["user_id"] == user_id
            assert "api_keys" in result
            assert "mongodb_connection" in result
            assert result["overall_status"] == "valid"
    
    @pytest.mark.asyncio
    async def test_user_not_found(self, config_service):
        """Test handling of non-existent user"""
        user_id = "nonexistent"
        
        with patch.object(config_service.auth_service, 'get_user_by_id') as mock_get_user:
            mock_get_user.return_value = None
            
            # Execute and verify exception
            with pytest.raises(HTTPException) as exc_info:
                await config_service.get_user_config(user_id)
            
            assert exc_info.value.status_code == 404
            assert "User not found" in str(exc_info.value.detail)


class TestEncryptionIntegration:
    """Test encryption/decryption integration"""
    
    def test_encrypt_decrypt_api_key(self):
        """Test API key encryption and decryption"""
        original_key = "sk-test123456789012345678901234567890"
        
        # Encrypt
        encrypted_key = encryption_service.encrypt(original_key)
        assert encrypted_key != original_key
        assert len(encrypted_key) > 0
        
        # Decrypt
        decrypted_key = encryption_service.decrypt(encrypted_key)
        assert decrypted_key == original_key
    
    def test_encrypt_decrypt_connection_string(self):
        """Test MongoDB connection string encryption and decryption"""
        original_connection = "mongodb://user:pass@localhost:27017/database"
        
        # Encrypt
        encrypted_connection = encryption_service.encrypt(original_connection)
        assert encrypted_connection != original_connection
        assert len(encrypted_connection) > 0
        
        # Decrypt
        decrypted_connection = encryption_service.decrypt(encrypted_connection)
        assert decrypted_connection == original_connection
    
    def test_encrypt_decrypt_dict(self):
        """Test dictionary encryption and decryption"""
        original_dict = {
            "openai": "sk-test123456789012345678901234567890",
            "gemini": "test-gemini-key-123456789"
        }
        
        # Encrypt
        encrypted_dict = encryption_service.encrypt_dict(original_dict)
        assert encrypted_dict != original_dict
        for key, value in encrypted_dict.items():
            assert value != original_dict[key]
        
        # Decrypt
        decrypted_dict = encryption_service.decrypt_dict(encrypted_dict)
        assert decrypted_dict == original_dict
    
    def test_encrypt_empty_string(self):
        """Test encryption of empty string"""
        encrypted = encryption_service.encrypt("")
        decrypted = encryption_service.decrypt(encrypted)
        assert decrypted == ""
    
    def test_decrypt_invalid_data(self):
        """Test decryption of invalid data"""
        decrypted = encryption_service.decrypt("invalid_encrypted_data")
        assert decrypted == ""  # Should return empty string on failure


if __name__ == "__main__":
    pytest.main([__file__])