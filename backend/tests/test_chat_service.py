"""Unit tests for chat service"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from bson import ObjectId

from services.chat_service import ChatService, chat_service
from models.chat import ChatSession, Message, ChatSessionCreate, MessageCreateValidated
from models.user import User


class TestChatService:
    """Test cases for ChatService class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.chat_service = ChatService()
        self.user_id = str(ObjectId())
        self.user_connection = "mongodb://localhost:27017/test_db"
        self.chat_id = str(ObjectId())
        
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

    @pytest.mark.asyncio
    async def test_create_chat_session_success(self):
        """Test successful chat session creation"""
        with patch.object(self.chat_service.db_router, 'create_chat_session', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = self.chat_id
            
            result = await self.chat_service.create_chat_session(
                user_id=self.user_id,
                user_connection=self.user_connection,
                title="Test Chat"
            )
            
            assert result.user_id == self.user_id
            assert result.title == "Test Chat"
            assert result.id == self.chat_id
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_chat_session_with_default_title(self):
        """Test chat session creation with default title"""
        with patch.object(self.chat_service.db_router, 'create_chat_session', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = self.chat_id
            
            result = await self.chat_service.create_chat_session(
                user_id=self.user_id,
                user_connection=self.user_connection
            )
            
            assert result.user_id == self.user_id
            assert "Chat" in result.title
            assert result.id == self.chat_id
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_chat_session_invalid_title(self):
        """Test chat session creation with invalid title"""
        with pytest.raises(ValueError):
            # This should fail at validation level before hitting database
            ChatSessionCreate(title="")  # Empty title should fail validation

    @pytest.mark.asyncio
    async def test_get_user_chats_success(self):
        """Test successful retrieval of user chats"""
        mock_chats = [self.mock_chat]
        
        with patch.object(self.chat_service.db_router, 'get_user_chat_sessions', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_chats
            
            result = await self.chat_service.get_user_chats(
                user_id=self.user_id,
                user_connection=self.user_connection
            )
            
            assert len(result) == 1
            assert result[0].id == self.mock_chat.id
            mock_get.assert_called_once_with(
                user_id=self.user_id,
                user_connection=self.user_connection,
                limit=None
            )

    @pytest.mark.asyncio
    async def test_get_user_chats_with_limit(self):
        """Test retrieval of user chats with limit"""
        mock_chats = [self.mock_chat]
        
        with patch.object(self.chat_service.db_router, 'get_user_chat_sessions', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_chats
            
            result = await self.chat_service.get_user_chats(
                user_id=self.user_id,
                user_connection=self.user_connection,
                limit=10
            )
            
            assert len(result) == 1
            mock_get.assert_called_once_with(
                user_id=self.user_id,
                user_connection=self.user_connection,
                limit=10
            )

    @pytest.mark.asyncio
    async def test_get_chat_session_success(self):
        """Test successful retrieval of specific chat session"""
        with patch.object(self.chat_service.db_router, 'get_chat_session', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = self.mock_chat
            
            result = await self.chat_service.get_chat_session(
                chat_id=self.chat_id,
                user_id=self.user_id,
                user_connection=self.user_connection
            )
            
            assert result.id == self.mock_chat.id
            assert result.user_id == self.user_id
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_chat_session_not_found(self):
        """Test retrieval of non-existent chat session"""
        with patch.object(self.chat_service.db_router, 'get_chat_session', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            result = await self.chat_service.get_chat_session(
                chat_id=self.chat_id,
                user_id=self.user_id,
                user_connection=self.user_connection
            )
            
            assert result is None
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_chat_messages_success(self):
        """Test successful retrieval of chat messages"""
        mock_messages = [self.mock_message]
        
        with patch.object(self.chat_service, 'get_chat_session', new_callable=AsyncMock) as mock_get_chat:
            with patch.object(self.chat_service.db_router, 'get_chat_messages', new_callable=AsyncMock) as mock_get_messages:
                mock_get_chat.return_value = self.mock_chat
                mock_get_messages.return_value = mock_messages
                
                result = await self.chat_service.get_chat_messages(
                    chat_id=self.chat_id,
                    user_id=self.user_id,
                    user_connection=self.user_connection
                )
                
                assert len(result) == 1
                assert result[0].id == self.mock_message.id
                mock_get_chat.assert_called_once()
                mock_get_messages.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_chat_messages_chat_not_found(self):
        """Test retrieval of messages for non-existent chat"""
        with patch.object(self.chat_service, 'get_chat_session', new_callable=AsyncMock) as mock_get_chat:
            mock_get_chat.return_value = None
            
            with pytest.raises(ValueError, match="Chat session .* not found or access denied"):
                await self.chat_service.get_chat_messages(
                    chat_id=self.chat_id,
                    user_id=self.user_id,
                    user_connection=self.user_connection
                )

    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """Test successful message sending"""
        message_id = str(ObjectId())
        
        with patch.object(self.chat_service, 'get_chat_session', new_callable=AsyncMock) as mock_get_chat:
            with patch.object(self.chat_service.db_router, 'create_message', new_callable=AsyncMock) as mock_create_message:
                with patch.object(self.chat_service, 'update_chat_session', new_callable=AsyncMock) as mock_update_chat:
                    mock_get_chat.return_value = self.mock_chat
                    mock_create_message.return_value = message_id
                    mock_update_chat.return_value = True
                    
                    result = await self.chat_service.send_message(
                        chat_id=self.chat_id,
                        user_id=self.user_id,
                        user_connection=self.user_connection,
                        content="Test message",
                        role="user"
                    )
                    
                    assert result.chat_id == self.chat_id
                    assert result.content == "Test message"
                    assert result.role == "user"
                    assert result.id == message_id
                    mock_get_chat.assert_called_once()
                    mock_create_message.assert_called_once()
                    mock_update_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_invalid_content(self):
        """Test sending message with invalid content"""
        with pytest.raises(ValueError):
            # This should fail at validation level before hitting database
            MessageCreateValidated(content="", role="user")  # Empty content should fail validation

    @pytest.mark.asyncio
    async def test_send_message_chat_not_found(self):
        """Test sending message to non-existent chat"""
        with patch.object(self.chat_service, 'get_chat_session', new_callable=AsyncMock) as mock_get_chat:
            mock_get_chat.return_value = None
            
            with pytest.raises(ValueError, match="Chat session .* not found or access denied"):
                await self.chat_service.send_message(
                    chat_id=self.chat_id,
                    user_id=self.user_id,
                    user_connection=self.user_connection,
                    content="Test message",
                    role="user"
                )

    @pytest.mark.asyncio
    async def test_update_chat_session_success(self):
        """Test successful chat session update"""
        update_data = {"title": "Updated Title"}
        
        with patch.object(self.chat_service, 'get_chat_session', new_callable=AsyncMock) as mock_get_chat:
            with patch.object(self.chat_service.db_router, 'update_chat_session', new_callable=AsyncMock) as mock_update:
                mock_get_chat.return_value = self.mock_chat
                mock_update.return_value = True
                
                result = await self.chat_service.update_chat_session(
                    chat_id=self.chat_id,
                    user_id=self.user_id,
                    user_connection=self.user_connection,
                    update_data=update_data
                )
                
                assert result is True
                mock_get_chat.assert_called_once()
                mock_update.assert_called_once()
                
                # Check that updated_at was added to update_data
                call_args = mock_update.call_args[1]
                assert "updated_at" in call_args["update_data"]

    @pytest.mark.asyncio
    async def test_update_chat_session_not_found(self):
        """Test updating non-existent chat session"""
        update_data = {"title": "Updated Title"}
        
        with patch.object(self.chat_service, 'get_chat_session', new_callable=AsyncMock) as mock_get_chat:
            mock_get_chat.return_value = None
            
            with pytest.raises(ValueError, match="Chat session .* not found or access denied"):
                await self.chat_service.update_chat_session(
                    chat_id=self.chat_id,
                    user_id=self.user_id,
                    user_connection=self.user_connection,
                    update_data=update_data
                )

    @pytest.mark.asyncio
    async def test_delete_chat_session_success(self):
        """Test successful chat session deletion"""
        with patch.object(self.chat_service, 'get_chat_session', new_callable=AsyncMock) as mock_get_chat:
            with patch.object(self.chat_service.db_router, 'delete_chat_session', new_callable=AsyncMock) as mock_delete:
                mock_get_chat.return_value = self.mock_chat
                mock_delete.return_value = True
                
                result = await self.chat_service.delete_chat_session(
                    chat_id=self.chat_id,
                    user_id=self.user_id,
                    user_connection=self.user_connection
                )
                
                assert result is True
                mock_get_chat.assert_called_once()
                mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_chat_session_not_found(self):
        """Test deleting non-existent chat session"""
        with patch.object(self.chat_service, 'get_chat_session', new_callable=AsyncMock) as mock_get_chat:
            mock_get_chat.return_value = None
            
            with pytest.raises(ValueError, match="Chat session .* not found or access denied"):
                await self.chat_service.delete_chat_session(
                    chat_id=self.chat_id,
                    user_id=self.user_id,
                    user_connection=self.user_connection
                )

    @pytest.mark.asyncio
    async def test_validate_user_access_to_chat_success(self):
        """Test successful user access validation"""
        with patch.object(self.chat_service, 'get_chat_session', new_callable=AsyncMock) as mock_get_chat:
            mock_get_chat.return_value = self.mock_chat
            
            result = await self.chat_service.validate_user_access_to_chat(
                chat_id=self.chat_id,
                user_id=self.user_id,
                user_connection=self.user_connection
            )
            
            assert result is True
            mock_get_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_user_access_to_chat_denied(self):
        """Test user access validation denial"""
        # Create a chat with different user_id
        different_chat = ChatSession(
            id=ObjectId(self.chat_id),
            user_id=str(ObjectId()),  # Different user ID
            title="Test Chat",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        with patch.object(self.chat_service, 'get_chat_session', new_callable=AsyncMock) as mock_get_chat:
            mock_get_chat.return_value = different_chat
            
            result = await self.chat_service.validate_user_access_to_chat(
                chat_id=self.chat_id,
                user_id=self.user_id,
                user_connection=self.user_connection
            )
            
            assert result is False

    @pytest.mark.asyncio
    async def test_validate_user_access_to_chat_not_found(self):
        """Test user access validation for non-existent chat"""
        with patch.object(self.chat_service, 'get_chat_session', new_callable=AsyncMock) as mock_get_chat:
            mock_get_chat.return_value = None
            
            result = await self.chat_service.validate_user_access_to_chat(
                chat_id=self.chat_id,
                user_id=self.user_id,
                user_connection=self.user_connection
            )
            
            assert result is False

    @pytest.mark.asyncio
    async def test_get_chat_statistics_success(self):
        """Test successful chat statistics retrieval"""
        mock_chats = [self.mock_chat]
        mock_messages = [self.mock_message]
        
        with patch.object(self.chat_service, 'get_user_chats', new_callable=AsyncMock) as mock_get_chats:
            with patch.object(self.chat_service, 'get_chat_messages', new_callable=AsyncMock) as mock_get_messages:
                mock_get_chats.return_value = mock_chats
                mock_get_messages.return_value = mock_messages
                
                result = await self.chat_service.get_chat_statistics(
                    user_id=self.user_id,
                    user_connection=self.user_connection
                )
                
                assert result["total_chats"] == 1
                assert result["chats_with_documents"] == 0  # No document_name set
                assert result["total_messages"] == 1
                assert result["average_messages_per_chat"] == 1.0
                
                mock_get_chats.assert_called_once()
                mock_get_messages.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_chat_statistics_no_chats(self):
        """Test chat statistics with no chats"""
        with patch.object(self.chat_service, 'get_user_chats', new_callable=AsyncMock) as mock_get_chats:
            mock_get_chats.return_value = []
            
            result = await self.chat_service.get_chat_statistics(
                user_id=self.user_id,
                user_connection=self.user_connection
            )
            
            assert result["total_chats"] == 0
            assert result["chats_with_documents"] == 0
            assert result["total_messages"] == 0
            assert result["average_messages_per_chat"] == 0

    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """Test error handling for database operations"""
        with patch.object(self.chat_service.db_router, 'create_chat_session', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("Database connection failed")
            
            with pytest.raises(Exception, match="Database connection failed"):
                await self.chat_service.create_chat_session(
                    user_id=self.user_id,
                    user_connection=self.user_connection,
                    title="Test Chat"
                )


class TestChatServiceIntegration:
    """Integration tests for ChatService with database router"""

    def setup_method(self):
        """Set up test fixtures"""
        self.user_id = str(ObjectId())
        self.user_connection = "mongodb://localhost:27017/test_db"

    @pytest.mark.asyncio
    async def test_chat_service_singleton(self):
        """Test that chat_service is properly instantiated"""
        assert chat_service is not None
        assert isinstance(chat_service, ChatService)
        assert hasattr(chat_service, 'db_router')

    @pytest.mark.asyncio
    async def test_dual_database_routing(self):
        """Test that chat service properly routes to user database"""
        with patch.object(chat_service.db_router, 'create_chat_session', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = str(ObjectId())
            
            await chat_service.create_chat_session(
                user_id=self.user_id,
                user_connection=self.user_connection,
                title="Test Chat"
            )
            
            # Verify that the database router was called with user database parameters
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            assert call_args[1]['user_id'] == self.user_id
            assert call_args[1]['user_connection'] == self.user_connection

    @pytest.mark.asyncio
    async def test_message_context_handling(self):
        """Test message creation with context"""
        chat_id = str(ObjectId())
        context_chunks = ["chunk1", "chunk2"]
        
        with patch.object(chat_service, 'get_chat_session', new_callable=AsyncMock) as mock_get_chat:
            with patch.object(chat_service.db_router, 'create_message', new_callable=AsyncMock) as mock_create_message:
                with patch.object(chat_service, 'update_chat_session', new_callable=AsyncMock) as mock_update_chat:
                    mock_chat = ChatSession(
                        id=ObjectId(chat_id),
                        user_id=self.user_id,
                        title="Test Chat",
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    mock_get_chat.return_value = mock_chat
                    mock_create_message.return_value = str(ObjectId())
                    mock_update_chat.return_value = True
                    
                    result = await chat_service.send_message(
                        chat_id=chat_id,
                        user_id=self.user_id,
                        user_connection=self.user_connection,
                        content="Test message with context",
                        role="assistant",
                        context_used=context_chunks
                    )
                    
                    assert result.context_used == context_chunks
                    assert result.role == "assistant"
                    mock_create_message.assert_called_once()