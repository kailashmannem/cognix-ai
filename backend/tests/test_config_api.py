"""Tests for configuration API endpoints"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from main import app
from models.user import User, UserConfig


class TestConfigAPI:
    """Test cases for configuration API endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        return User(
            id="507f1f77bcf86cd799439011",
            email="test@example.com",
            password_hash="hashed_password",
            api_keys={},
            user_mongodb_connection=None,
            preferred_llm_provider="openai",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer test_token"}
    
    def test_get_user_config_success(self, client, mock_user, auth_headers):
        """Test successful retrieval of user configuration"""
        mock_config = {
            "api_keys": {
                "openai": {"masked": "sk-test...1234", "configured": True}
            },
            "mongodb_connection": {"configured": False},
            "preferred_llm_provider": "openai",
            "updated_at": datetime.utcnow()
        }
        
        with patch('routers.config.get_current_user') as mock_get_user, \
             patch('routers.config.config_service') as mock_service:
            
            mock_get_user.return_value = mock_user
            mock_service.get_user_config = AsyncMock(return_value=mock_config)
            
            response = client.get("/api/user/config", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert "api_keys" in data
            assert "mongodb_connection" in data
            assert "preferred_llm_provider" in data
            assert data["preferred_llm_provider"] == "openai"
    
    def test_update_user_config_success(self, client, mock_user, auth_headers):
        """Test successful user configuration update"""
        config_data = {
            "api_keys": {
                "openai": "sk-test123456789012345678901234567890"
            },
            "preferred_llm_provider": "openai"
        }
        
        mock_result = {
            "success": True,
            "validation_results": {
                "api_keys": {
                    "openai": {"valid": True}
                }
            },
            "updated_fields": ["api_keys", "preferred_llm_provider", "updated_at"]
        }
        
        with patch('routers.config.get_current_user') as mock_get_user, \
             patch('routers.config.config_service') as mock_service:
            
            mock_get_user.return_value = mock_user
            mock_service.update_user_config = AsyncMock(return_value=mock_result)
            
            response = client.put("/api/user/config", json=config_data, headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "validation_results" in data
    
    def test_delete_api_key_success(self, client, mock_user, auth_headers):
        """Test successful API key deletion"""
        provider = "openai"
        
        with patch('routers.config.get_current_user') as mock_get_user, \
             patch('routers.config.config_service') as mock_service:
            
            mock_get_user.return_value = mock_user
            mock_service.delete_api_key = AsyncMock(return_value=True)
            
            response = client.delete(f"/api/user/config/api-key/{provider}", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert f"API key for {provider} deleted successfully" in data["message"]


if __name__ == "__main__":
    pytest.main([__file__])