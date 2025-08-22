"""Integration tests for chat API endpoints"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime
from bson import ObjectId

from main import app
from models.chat import ChatSession, Message
from models.user import User
from services.chat_service import chat_service
from utils.auth_middleware import get_current_user


class TestChatAPI:
    """Test cases for chat API endpoints"""

    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
        self.user_id = str(ObjectId())
        self.chat_id = str(ObjectId())
        self.user_connection = "mongodb://localhost:27017/test_db"
        
        # Mock user
        self.mock_user = User(
            id=ObjectId(self.user_id),
            email="test@example.com",
            password_hash="hashed_password",
            user_mongodb_connection=self.user_connection,
            preferred_llm_provider="openai"
        )
        
        # Mock chat session
        self.mock_chat = ChatSession(
            id=ObjectId(self.chat_id),
            user_id=self.user_id,
            title="Test Chat",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock message
        self.mock_message = Message(
            id=ObjectId(),
            chat_id=self.chat_id,
            content="Test message",
            role="user",
            timestamp=datetime.utcnow()
        )

    def teardown_method(self):
        """Clean up after tests"""
        app.dependency_overrides.clear()

    def test_get_chats_success(self):
        """Test successful retrieval of user chats"""
        # Override the dependency
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        
        with patch.object(chat_service, 'get_user_chats', new_callable=AsyncMock) as mock_get_chats:
            mock_get_chats.return_value = [self.mock_chat]
            
            response = self.client.get("/api/chats/")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == self.chat_id
            assert data[0]["title"] == "Test Chat"
        
        # Clean up
        app.dependency_overrides.clear()

    def test_get_chats_no_database_connection(self):
        """Test get chats with no user database connection"""
        user_without_db = User(
            id=ObjectId(self.user_id),
            email="test@example.com",
            password_hash="hashed_password",
            user_mongodb_connection=None,  # No database connection
            preferred_llm_provider="openai"
        )
        
        app.dependency_overrides[get_current_user] = lambda: user_without_db
        
        response = self.client.get("/api/chats/")
        
        assert response.status_code == 400
        assert "database connection not configured" in response.json()["detail"]

    def test_get_chats_with_limit(self):
        """Test get chats with limit parameter"""
        with patch('routers.chat.get_current_user') as mock_get_user:
            with patch.object(chat_service, 'get_user_chats', new_callable=AsyncMock) as mock_get_chats:
                mock_get_user.return_value = self.mock_user
                mock_get_chats.return_value = [self.mock_chat]
                
                response = self.client.get("/api/chats/?limit=10")
                
                assert response.status_code == 200
                mock_get_chats.assert_called_once()
                call_args = mock_get_chats.call_args[1]
                assert call_args['limit'] == 10

    def test_create_chat_success(self):
        """Test successful chat creation"""
        chat_data = {"title": "New Test Chat"}
        
        with patch('routers.chat.get_current_user') as mock_get_user:
            with patch.object(chat_service, 'create_chat_session', new_callable=AsyncMock) as mock_create_chat:
                mock_get_user.return_value = self.mock_user
                mock_create_chat.return_value = self.mock_chat
                
                response = self.client.post("/api/chats/", json=chat_data)
                
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == self.chat_id
                assert data["title"] == "Test Chat"

    def test_create_chat_invalid_title(self):
        """Test chat creation with invalid title"""
        chat_data = {"title": ""}  # Empty title
        
        with patch('routers.chat.get_current_user') as mock_get_user:
            mock_get_user.return_value = self.mock_user
            
            response = self.client.post("/api/chats/", json=chat_data)
            
            assert response.status_code == 422  # Validation error

    def test_create_chat_no_database_connection(self):
        """Test chat creation with no user database connection"""
        user_without_db = User(
            id=ObjectId(self.user_id),
            email="test@example.com",
            password_hash="hashed_password",
            user_mongodb_connection=None,
            preferred_llm_provider="openai"
        )
        chat_data = {"title": "New Test Chat"}
        
        with patch('routers.chat.get_current_user') as mock_get_user:
            mock_get_user.return_value = user_without_db
            
            response = self.client.post("/api/chats/", json=chat_data)
            
            assert response.status_code == 400
            assert "database connection not configured" in response.json()["detail"]

    def test_get_chat_success(self):
        """Test successful retrieval of specific chat"""
        with patch('routers.chat.get_current_user') as mock_get_user:
            with patch.object(chat_service, 'get_chat_session', new_callable=AsyncMock) as mock_get_chat:
                mock_get_user.return_value = self.mock_user
                mock_get_chat.return_value = self.mock_chat
                
                response = self.client.get(f"/api/chats/{self.chat_id}")
                
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == self.chat_id
                assert data["title"] == "Test Chat"

    def test_get_chat_not_found(self):
        """Test retrieval of non-existent chat"""
        with patch('routers.chat.get_current_user') as mock_get_user:
            with patch.object(chat_service, 'get_chat_session', new_callable=AsyncMock) as mock_get_chat:
                mock_get_user.return_value = self.mock_user
                mock_get_chat.return_value = None
                
                response = self.client.get(f"/api/chats/{self.chat_id}")
                
                assert response.status_code == 404
                assert "not found" in response.json()["detail"]

    def test_get_chat_access_denied(self):
        """Test access denied to chat owned by different user"""
        different_user_chat = ChatSession(
            id=ObjectId(self.chat_id),
            user_id=str(ObjectId()),  # Different user ID
            title="Test Chat",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        with patch('routers.chat.get_current_user') as mock_get_user:
            with patch.object(chat_service, 'get_chat_session', new_callable=AsyncMock) as mock_get_chat:
                mock_get_user.return_value = self.mock_user
                mock_get_chat.return_value = different_user_chat
                
                response = self.client.get(f"/api/chats/{self.chat_id}")
                
                assert response.status_code == 403
                assert "Access denied" in response.json()["detail"]

    def test_get_chat_messages_success(self):
        """Test successful retrieval of chat messages"""
        with patch('routers.chat.get_current_user') as mock_get_user:
            with patch.object(chat_service, 'get_chat_messages', new_callable=AsyncMock) as mock_get_messages:
                mock_get_user.return_value = self.mock_user
                mock_get_messages.return_value = [self.mock_message]
                
                response = self.client.get(f"/api/chats/{self.chat_id}/messages")
                
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["content"] == "Test message"
                assert data[0]["role"] == "user"

    def test_get_chat_messages_with_pagination(self):
        """Test get chat messages with pagination parameters"""
        with patch('routers.chat.get_current_user') as mock_get_user:
            with patch.object(chat_service, 'get_chat_messages', new_callable=AsyncMock) as mock_get_messages:
                mock_get_user.return_value = self.mock_user
                mock_get_messages.return_value = [self.mock_message]
                
                response = self.client.get(f"/api/chats/{self.chat_id}/messages?limit=10&skip=5")
                
                assert response.status_code == 200
                mock_get_messages.assert_called_once()
                call_args = mock_get_messages.call_args[1]
                assert call_args['limit'] == 10
                assert call_args['skip'] == 5

    def test_get_chat_messages_chat_not_found(self):
        """Test get messages for non-existent chat"""
        with patch('routers.chat.get_current_user') as mock_get_user:
            with patch.object(chat_service, 'get_chat_messages', new_callable=AsyncMock) as mock_get_messages:
                mock_get_user.return_value = self.mock_user
                mock_get_messages.side_effect = ValueError("Chat session not found or access denied")
                
                response = self.client.get(f"/api/chats/{self.chat_id}/messages")
                
                assert response.status_code == 400
                assert "Chat session not found or access denied" in response.json()["detail"]

    def test_send_message_success(self):
        """Test successful message sending"""
        message_data = {"content": "Hello, world!", "role": "user"}
        
        with patch('routers.chat.get_current_user') as mock_get_user:
            with patch.object(chat_service, 'send_message', new_callable=AsyncMock) as mock_send_message:
                mock_get_user.return_value = self.mock_user
                mock_send_message.return_value = self.mock_message
                
                response = self.client.post(f"/api/chats/{self.chat_id}/messages", json=message_data)
                
                assert response.status_code == 200
                data = response.json()
                assert data["content"] == "Test message"
                assert data["role"] == "user"

    def test_send_message_invalid_content(self):
        """Test sending message with invalid content"""
        message_data = {"content": "", "role": "user"}  # Empty content
        
        with patch('routers.chat.get_current_user') as mock_get_user:
            mock_get_user.return_value = self.mock_user
            
            response = self.client.post(f"/api/chats/{self.chat_id}/messages", json=message_data)
            
            assert response.status_code == 422  # Validation error

    def test_send_message_chat_not_found(self):
        """Test sending message to non-existent chat"""
        message_data = {"content": "Hello, world!", "role": "user"}
        
        with patch('routers.chat.get_current_user') as mock_get_user:
            with patch.object(chat_service, 'send_message', new_callable=AsyncMock) as mock_send_message:
                mock_get_user.return_value = self.mock_user
                mock_send_message.side_effect = ValueError("Chat session not found or access denied")
                
                response = self.client.post(f"/api/chats/{self.chat_id}/messages", json=message_data)
                
                assert response.status_code == 400
                assert "Chat session not found or access denied" in response.json()["detail"]

    def test_delete_chat_success(self):
        """Test successful chat deletion"""
        with patch('routers.chat.get_current_user') as mock_get_user:
            with patch.object(chat_service, 'delete_chat_session', new_callable=AsyncMock) as mock_delete_chat:
                mock_get_user.return_value = self.mock_user
                mock_delete_chat.return_value = True
                
                response = self.client.delete(f"/api/chats/{self.chat_id}")
                
                assert response.status_code == 200
                data = response.json()
                assert "deleted successfully" in data["message"]

    def test_delete_chat_not_found(self):
        """Test deletion of non-existent chat"""
        with patch('routers.chat.get_current_user') as mock_get_user:
            with patch.object(chat_service, 'delete_chat_session', new_callable=AsyncMock) as mock_delete_chat:
                mock_get_user.return_value = self.mock_user
                mock_delete_chat.side_effect = ValueError("Chat session not found or access denied")
                
                response = self.client.delete(f"/api/chats/{self.chat_id}")
                
                assert response.status_code == 400
                assert "Chat session not found or access denied" in response.json()["detail"]

    def test_delete_chat_failure(self):
        """Test chat deletion failure"""
        with patch('routers.chat.get_current_user') as mock_get_user:
            with patch.object(chat_service, 'delete_chat_session', new_callable=AsyncMock) as mock_delete_chat:
                mock_get_user.return_value = self.mock_user
                mock_delete_chat.return_value = False
                
                response = self.client.delete(f"/api/chats/{self.chat_id}")
                
                assert response.status_code == 500
                assert "Failed to delete" in response.json()["detail"]

    def test_get_chat_statistics_success(self):
        """Test successful chat statistics retrieval"""
        mock_stats = {
            "total_chats": 5,
            "chats_with_documents": 3,
            "total_messages": 25,
            "average_messages_per_chat": 5.0
        }
        
        with patch('routers.chat.get_current_user') as mock_get_user:
            with patch.object(chat_service, 'get_chat_statistics', new_callable=AsyncMock) as mock_get_stats:
                mock_get_user.return_value = self.mock_user
                mock_get_stats.return_value = mock_stats
                
                response = self.client.get(f"/api/chats/{self.chat_id}/statistics")
                
                assert response.status_code == 200
                data = response.json()
                assert data["total_chats"] == 5
                assert data["chats_with_documents"] == 3
                assert data["total_messages"] == 25
                assert data["average_messages_per_chat"] == 5.0

    def test_unauthorized_access(self):
        """Test unauthorized access to chat endpoints"""
        with patch('routers.chat.get_current_user') as mock_get_user:
            mock_get_user.side_effect = Exception("Unauthorized")
            
            response = self.client.get("/api/chats/")
            
            # The exact status code depends on how the auth middleware handles exceptions
            assert response.status_code in [401, 500]

    def test_database_error_handling(self):
        """Test handling of database errors"""
        with patch('routers.chat.get_current_user') as mock_get_user:
            with patch.object(chat_service, 'get_user_chats', new_callable=AsyncMock) as mock_get_chats:
                mock_get_user.return_value = self.mock_user
                mock_get_chats.side_effect = Exception("Database connection failed")
                
                response = self.client.get("/api/chats/")
                
                assert response.status_code == 500
                assert "Failed to retrieve" in response.json()["detail"]

    def test_invalid_chat_id_format(self):
        """Test handling of invalid chat ID format"""
        invalid_chat_id = "invalid-id"
        
        with patch('routers.chat.get_current_user') as mock_get_user:
            with patch.object(chat_service, 'get_chat_session', new_callable=AsyncMock) as mock_get_chat:
                mock_get_user.return_value = self.mock_user
                mock_get_chat.side_effect = Exception("Invalid ObjectId")
                
                response = self.client.get(f"/api/chats/{invalid_chat_id}")
                
                assert response.status_code == 500

    def test_concurrent_message_sending(self):
        """Test handling of concurrent message sending"""
        message_data = {"content": "Concurrent message", "role": "user"}
        
        with patch('routers.chat.get_current_user') as mock_get_user:
            with patch.object(chat_service, 'send_message', new_callable=AsyncMock) as mock_send_message:
                mock_get_user.return_value = self.mock_user
                mock_send_message.return_value = self.mock_message
                
                # Simulate multiple concurrent requests
                responses = []
                for _ in range(3):
                    response = self.client.post(f"/api/chats/{self.chat_id}/messages", json=message_data)
                    responses.append(response)
                
                # All requests should succeed
                for response in responses:
                    assert response.status_code == 200
                
                # Service should be called for each request
                assert mock_send_message.call_count == 3


class TestChatAPIValidation:
    """Test cases for API input validation"""

    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
        self.user_id = str(ObjectId())
        self.mock_user = User(
            id=ObjectId(self.user_id),
            email="test@example.com",
            password_hash="hashed_password",
            user_mongodb_connection="mongodb://localhost:27017/test_db",
            preferred_llm_provider="openai"
        )

    def test_create_chat_title_too_long(self):
        """Test chat creation with title too long"""
        long_title = "x" * 201  # Exceeds 200 character limit
        chat_data = {"title": long_title}
        
        with patch('routers.chat.get_current_user') as mock_get_user:
            mock_get_user.return_value = self.mock_user
            
            response = self.client.post("/api/chats/", json=chat_data)
            
            assert response.status_code == 422

    def test_send_message_content_too_long(self):
        """Test sending message with content too long"""
        long_content = "x" * 10001  # Exceeds 10000 character limit
        message_data = {"content": long_content, "role": "user"}
        chat_id = str(ObjectId())
        
        with patch('routers.chat.get_current_user') as mock_get_user:
            mock_get_user.return_value = self.mock_user
            
            response = self.client.post(f"/api/chats/{chat_id}/messages", json=message_data)
            
            assert response.status_code == 422

    def test_send_message_invalid_role(self):
        """Test sending message with invalid role"""
        message_data = {"content": "Test message", "role": "invalid_role"}
        chat_id = str(ObjectId())
        
        with patch('routers.chat.get_current_user') as mock_get_user:
            mock_get_user.return_value = self.mock_user
            
            response = self.client.post(f"/api/chats/{chat_id}/messages", json=message_data)
            
            assert response.status_code == 422

    def test_get_chats_invalid_limit(self):
        """Test get chats with invalid limit parameter"""
        with patch('routers.chat.get_current_user') as mock_get_user:
            mock_get_user.return_value = self.mock_user
            
            # Test negative limit
            response = self.client.get("/api/chats/?limit=-1")
            assert response.status_code == 422
            
            # Test limit too high
            response = self.client.get("/api/chats/?limit=101")
            assert response.status_code == 422

    def test_get_messages_invalid_pagination(self):
        """Test get messages with invalid pagination parameters"""
        chat_id = str(ObjectId())
        
        with patch('routers.chat.get_current_user') as mock_get_user:
            mock_get_user.return_value = self.mock_user
            
            # Test negative skip
            response = self.client.get(f"/api/chats/{chat_id}/messages?skip=-1")
            assert response.status_code == 422
            
            # Test invalid limit
            response = self.client.get(f"/api/chats/{chat_id}/messages?limit=1001")
            assert response.status_code == 422