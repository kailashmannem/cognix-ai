"""Tests for database models and dual database architecture"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from models.user import User, UserCreate, UserConfig, UserValidation
from models.chat import ChatSession, Message, ChatValidation, ChatSessionCreate, MessageCreateValidated
from models.document import Document, DocumentChunk, DocumentValidation, DocumentCreate, DocumentChunkCreate
from utils.model_utils import ModelValidator, ModelOperations
from utils.database import DatabaseManager
from utils.database_router import DatabaseRouter


class TestUserModel:
    """Test User model validation and serialization"""
    
    def test_user_model_creation(self):
        """Test creating a valid User model"""
        user_data = {
            "email": "test@example.com",
            "password_hash": "hashed_password",
            "api_keys": {"openai": "sk-test"},
            "preferred_llm_provider": "openai"
        }
        
        user = User(**user_data)
        assert user.email == "test@example.com"
        assert user.preferred_llm_provider == "openai"
        assert user.api_keys["openai"] == "sk-test"
    
    def test_user_config_validation(self):
        """Test UserConfig validation"""
        # Valid config
        config = UserConfig(
            preferred_llm_provider="openai",
            api_keys={"openai": "sk-test"},
            user_mongodb_connection="mongodb://localhost:27017/test"
        )
        assert config.preferred_llm_provider == "openai"
        
        # Invalid provider
        with pytest.raises(ValueError):
            UserConfig(preferred_llm_provider="invalid_provider")
        
        # Invalid connection string
        with pytest.raises(ValueError):
            UserConfig(user_mongodb_connection="invalid_connection")
    
    def test_password_validation(self):
        """Test password strength validation"""
        assert UserValidation.validate_password_strength("Password123") == True
        assert UserValidation.validate_password_strength("weak") == False
        assert UserValidation.validate_password_strength("NoNumbers!") == False
        assert UserValidation.validate_password_strength("nonumbers123") == False
    
    def test_email_validation(self):
        """Test email format validation"""
        assert UserValidation.validate_email_format("test@example.com") == True
        assert UserValidation.validate_email_format("invalid.email") == False
        assert UserValidation.validate_email_format("@example.com") == False


class TestChatModel:
    """Test Chat and Message model validation"""
    
    def test_chat_session_creation(self):
        """Test creating a valid ChatSession"""
        chat_data = {
            "user_id": "user123",
            "title": "Test Chat",
            "document_name": "test.pdf"
        }
        
        chat = ChatSession(**chat_data)
        assert chat.user_id == "user123"
        assert chat.title == "Test Chat"
        assert chat.document_name == "test.pdf"
    
    def test_message_creation(self):
        """Test creating a valid Message"""
        message_data = {
            "chat_id": "chat123",
            "content": "Hello, world!",
            "role": "user"
        }
        
        message = Message(**message_data)
        assert message.chat_id == "chat123"
        assert message.content == "Hello, world!"
        assert message.role == "user"
    
    def test_chat_validation(self):
        """Test chat validation methods"""
        assert ChatValidation.validate_chat_title("Valid Title") == True
        assert ChatValidation.validate_chat_title("") == False
        assert ChatValidation.validate_chat_title("x" * 201) == False
        
        assert ChatValidation.validate_message_content("Valid message") == True
        assert ChatValidation.validate_message_content("") == False
        assert ChatValidation.validate_message_content("x" * 10001) == False
        
        assert ChatValidation.validate_message_role("user") == True
        assert ChatValidation.validate_message_role("invalid") == False
    
    def test_enhanced_chat_models(self):
        """Test enhanced chat models with validation"""
        # Valid chat creation
        chat_create = ChatSessionCreate(title="Test Chat")
        assert chat_create.title == "Test Chat"
        
        # Invalid chat creation
        with pytest.raises(ValueError):
            ChatSessionCreate(title="")
        
        # Valid message creation
        message_create = MessageCreateValidated(content="Test message")
        assert message_create.content == "Test message"
        assert message_create.role == "user"
        
        # Invalid message creation
        with pytest.raises(ValueError):
            MessageCreateValidated(content="")


class TestDocumentModel:
    """Test Document and DocumentChunk model validation"""
    
    def test_document_creation(self):
        """Test creating a valid Document"""
        doc_data = {
            "chat_id": "chat123",
            "filename": "test.pdf",
            "file_type": "application/pdf",
            "file_size": 1024
        }
        
        document = Document(**doc_data)
        assert document.chat_id == "chat123"
        assert document.filename == "test.pdf"
        assert document.file_type == "application/pdf"
        assert document.file_size == 1024
    
    def test_document_chunk_creation(self):
        """Test creating a valid DocumentChunk"""
        chunk_data = {
            "document_id": "doc123",
            "chat_id": "chat123",
            "content": "This is a test chunk",
            "chunk_index": 0
        }
        
        chunk = DocumentChunk(**chunk_data)
        assert chunk.document_id == "doc123"
        assert chunk.content == "This is a test chunk"
        assert chunk.chunk_index == 0
    
    def test_document_validation(self):
        """Test document validation methods"""
        assert DocumentValidation.validate_file_extension("test.pdf") == True
        assert DocumentValidation.validate_file_extension("test.exe") == False
        
        assert DocumentValidation.validate_file_size(1024) == True
        assert DocumentValidation.validate_file_size(0) == False
        assert DocumentValidation.validate_file_size(11 * 1024 * 1024) == False
        
        assert DocumentValidation.validate_mime_type("application/pdf") == True
        assert DocumentValidation.validate_mime_type("application/exe") == False
        
        assert DocumentValidation.validate_processing_status("pending") == True
        assert DocumentValidation.validate_processing_status("invalid") == False
    
    def test_enhanced_document_models(self):
        """Test enhanced document models with validation"""
        # Valid document creation
        doc_create = DocumentCreate(
            filename="test.pdf",
            file_type="application/pdf",
            file_size=1024
        )
        assert doc_create.filename == "test.pdf"
        
        # Invalid document creation
        with pytest.raises(ValueError):
            DocumentCreate(
                filename="test.exe",
                file_type="application/pdf",
                file_size=1024
            )
        
        # Valid chunk creation
        chunk_create = DocumentChunkCreate(
            content="Test chunk content",
            chunk_index=0
        )
        assert chunk_create.content == "Test chunk content"
        
        # Invalid chunk creation
        with pytest.raises(ValueError):
            DocumentChunkCreate(content="", chunk_index=0)


class TestModelValidator:
    """Test ModelValidator utility methods"""
    
    def test_model_validation(self):
        """Test model validation"""
        user_data = {
            "email": "test@example.com",
            "password_hash": "hashed_password"
        }
        
        validator = ModelValidator()
        user = validator.validate_model(User, user_data)
        assert isinstance(user, User)
        assert user.email == "test@example.com"
    
    def test_mongo_serialization(self):
        """Test MongoDB serialization"""
        user = User(email="test@example.com", password_hash="hashed")
        validator = ModelValidator()
        
        serialized = validator.serialize_for_mongo(user)
        assert isinstance(serialized, dict)
        assert serialized["email"] == "test@example.com"
        
        # Test deserialization
        deserialized = validator.deserialize_from_mongo(User, serialized)
        assert isinstance(deserialized, User)
        assert deserialized.email == "test@example.com"
    
    def test_object_id_validation(self):
        """Test ObjectId validation"""
        validator = ModelValidator()
        
        # Valid ObjectId string
        valid_id = "507f1f77bcf86cd799439011"
        assert validator.validate_object_id(valid_id) == True
        
        # Invalid ObjectId string
        invalid_id = "invalid_id"
        assert validator.validate_object_id(invalid_id) == False


class TestDatabaseManager:
    """Test DatabaseManager functionality"""
    
    def test_database_routing(self):
        """Test database routing logic"""
        db_manager = DatabaseManager()
        
        # Test platform routing
        route = db_manager.route_to_database(operation_type="platform")
        assert route == "platform"
        
        # Test user routing
        route = db_manager.route_to_database(user_id="user123", operation_type="user")
        assert route == "user"
        
        # Test invalid routing
        with pytest.raises(ValueError):
            db_manager.route_to_database(operation_type="invalid")
    
    def test_connection_string_parsing(self):
        """Test connection string parsing"""
        db_manager = DatabaseManager()
        
        # Test with database name in path
        connection = "mongodb://localhost:27017/testdb"
        db_name = db_manager._extract_database_name(connection, "user123")
        assert db_name == "testdb"
        
        # Test without database name
        connection = "mongodb://localhost:27017"
        db_name = db_manager._extract_database_name(connection, "user123")
        assert db_name == "cognix_user_user123"


# Integration tests would require actual MongoDB connections
# These are placeholder tests for the structure

class TestDatabaseIntegration:
    """Integration tests for database operations"""
    
    @pytest.mark.asyncio
    async def test_connection_validation(self):
        """Test connection validation (requires MongoDB)"""
        # This would test actual MongoDB connections
        # Skipped in unit tests
        pass
    
    @pytest.mark.asyncio
    async def test_database_operations(self):
        """Test database CRUD operations (requires MongoDB)"""
        # This would test actual database operations
        # Skipped in unit tests
        pass


if __name__ == "__main__":
    # Run basic tests
    test_user = TestUserModel()
    test_user.test_user_model_creation()
    test_user.test_user_config_validation()
    test_user.test_password_validation()
    test_user.test_email_validation()
    
    test_chat = TestChatModel()
    test_chat.test_chat_session_creation()
    test_chat.test_message_creation()
    test_chat.test_chat_validation()
    test_chat.test_enhanced_chat_models()
    
    test_doc = TestDocumentModel()
    test_doc.test_document_creation()
    test_doc.test_document_chunk_creation()
    test_doc.test_document_validation()
    test_doc.test_enhanced_document_models()
    
    test_validator = TestModelValidator()
    test_validator.test_model_validation()
    test_validator.test_mongo_serialization()
    test_validator.test_object_id_validation()
    
    test_db = TestDatabaseManager()
    test_db.test_database_routing()
    test_db.test_connection_string_parsing()
    
    print("All tests passed!")