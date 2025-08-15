"""Database routing utilities for dual database architecture"""

from typing import Optional, Dict, Any, Type, TypeVar
from pydantic import BaseModel
import logging

from utils.database import db_manager
from utils.model_utils import ModelOperations, ModelValidator
from models.user import User
from models.chat import ChatSession, Message
from models.document import Document, DocumentChunk

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class DatabaseRouter:
    """Router for managing operations across platform and user databases"""
    
    def __init__(self):
        self.model_ops = ModelOperations(db_manager)
        self.validator = ModelValidator()
    
    # Platform Database Operations (User Authentication)
    
    async def create_user(self, user: User) -> str:
        """Create user in platform database"""
        return await self.model_ops.create_document(
            collection_name="users",
            model=user,
            operation_type="platform"
        )
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user from platform database by ID"""
        return await self.model_ops.get_document(
            collection_name="users",
            document_id=user_id,
            model_class=User,
            operation_type="platform"
        )
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user from platform database by email"""
        users = await self.model_ops.find_documents(
            collection_name="users",
            filter_dict={"email": email},
            model_class=User,
            limit=1,
            operation_type="platform"
        )
        return users[0] if users else None
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user in platform database"""
        return await self.model_ops.update_document(
            collection_name="users",
            document_id=user_id,
            update_data=update_data,
            operation_type="platform"
        )
    
    # User Database Operations (Personal Data)
    
    async def create_chat_session(self, chat_session: ChatSession, user_id: str, user_connection: str) -> str:
        """Create chat session in user's database"""
        return await self.model_ops.create_document(
            collection_name="chat_sessions",
            model=chat_session,
            user_id=user_id,
            operation_type="user",
            user_connection=user_connection
        )
    
    async def get_chat_session(self, chat_id: str, user_id: str, user_connection: str) -> Optional[ChatSession]:
        """Get chat session from user's database"""
        return await self.model_ops.get_document(
            collection_name="chat_sessions",
            document_id=chat_id,
            model_class=ChatSession,
            user_id=user_id,
            operation_type="user",
            user_connection=user_connection
        )
    
    async def get_user_chat_sessions(self, user_id: str, user_connection: str, limit: int = None) -> list[ChatSession]:
        """Get all chat sessions for a user from their database"""
        return await self.model_ops.find_documents(
            collection_name="chat_sessions",
            filter_dict={"user_id": user_id},
            model_class=ChatSession,
            limit=limit,
            sort=[("created_at", -1)],
            user_id=user_id,
            operation_type="user",
            user_connection=user_connection
        )
    
    async def update_chat_session(self, chat_id: str, update_data: Dict[str, Any], 
                                user_id: str, user_connection: str) -> bool:
        """Update chat session in user's database"""
        return await self.model_ops.update_document(
            collection_name="chat_sessions",
            document_id=chat_id,
            update_data=update_data,
            user_id=user_id,
            operation_type="user",
            user_connection=user_connection
        )
    
    async def delete_chat_session(self, chat_id: str, user_id: str, user_connection: str) -> bool:
        """Delete chat session and all related data from user's database"""
        try:
            # Delete all messages in the chat
            await self.delete_chat_messages(chat_id, user_id, user_connection)
            
            # Delete all documents and chunks in the chat
            await self.delete_chat_documents(chat_id, user_id, user_connection)
            
            # Delete the chat session itself
            return await self.model_ops.delete_document(
                collection_name="chat_sessions",
                document_id=chat_id,
                user_id=user_id,
                operation_type="user",
                user_connection=user_connection
            )
        except Exception as e:
            logger.error(f"Failed to delete chat session {chat_id}: {e}")
            raise
    
    async def create_message(self, message: Message, user_id: str, user_connection: str) -> str:
        """Create message in user's database"""
        return await self.model_ops.create_document(
            collection_name="messages",
            model=message,
            user_id=user_id,
            operation_type="user",
            user_connection=user_connection
        )
    
    async def get_chat_messages(self, chat_id: str, user_id: str, user_connection: str, 
                              limit: int = None, skip: int = None) -> list[Message]:
        """Get messages for a chat from user's database"""
        return await self.model_ops.find_documents(
            collection_name="messages",
            filter_dict={"chat_id": chat_id},
            model_class=Message,
            limit=limit,
            skip=skip,
            sort=[("timestamp", 1)],
            user_id=user_id,
            operation_type="user",
            user_connection=user_connection
        )
    
    async def delete_chat_messages(self, chat_id: str, user_id: str, user_connection: str) -> int:
        """Delete all messages for a chat from user's database"""
        try:
            db = await db_manager.get_database_for_operation(
                user_id=user_id,
                operation_type="user",
                user_connection=user_connection
            )
            
            result = await db.messages.delete_many({"chat_id": chat_id})
            logger.info(f"Deleted {result.deleted_count} messages for chat {chat_id}")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Failed to delete messages for chat {chat_id}: {e}")
            raise
    
    async def create_document(self, document: Document, user_id: str, user_connection: str) -> str:
        """Create document in user's database"""
        return await self.model_ops.create_document(
            collection_name="documents",
            model=document,
            user_id=user_id,
            operation_type="user",
            user_connection=user_connection
        )
    
    async def get_document(self, document_id: str, user_id: str, user_connection: str) -> Optional[Document]:
        """Get document from user's database"""
        return await self.model_ops.get_document(
            collection_name="documents",
            document_id=document_id,
            model_class=Document,
            user_id=user_id,
            operation_type="user",
            user_connection=user_connection
        )
    
    async def get_chat_documents(self, chat_id: str, user_id: str, user_connection: str) -> list[Document]:
        """Get all documents for a chat from user's database"""
        return await self.model_ops.find_documents(
            collection_name="documents",
            filter_dict={"chat_id": chat_id},
            model_class=Document,
            user_id=user_id,
            operation_type="user",
            user_connection=user_connection
        )
    
    async def update_document_status(self, document_id: str, status: str, 
                                   user_id: str, user_connection: str) -> bool:
        """Update document processing status in user's database"""
        return await self.model_ops.update_document(
            collection_name="documents",
            document_id=document_id,
            update_data={"processing_status": status},
            user_id=user_id,
            operation_type="user",
            user_connection=user_connection
        )
    
    async def delete_chat_documents(self, chat_id: str, user_id: str, user_connection: str) -> int:
        """Delete all documents and chunks for a chat from user's database"""
        try:
            db = await db_manager.get_database_for_operation(
                user_id=user_id,
                operation_type="user",
                user_connection=user_connection
            )
            
            # Get all documents for the chat
            documents = await self.get_chat_documents(chat_id, user_id, user_connection)
            
            # Delete all chunks for these documents
            total_chunks_deleted = 0
            for doc in documents:
                chunks_result = await db.document_chunks.delete_many({"document_id": str(doc.id)})
                total_chunks_deleted += chunks_result.deleted_count
            
            # Delete all documents for the chat
            docs_result = await db.documents.delete_many({"chat_id": chat_id})
            
            logger.info(f"Deleted {docs_result.deleted_count} documents and {total_chunks_deleted} chunks for chat {chat_id}")
            return docs_result.deleted_count
            
        except Exception as e:
            logger.error(f"Failed to delete documents for chat {chat_id}: {e}")
            raise
    
    async def create_document_chunk(self, chunk: DocumentChunk, user_id: str, user_connection: str) -> str:
        """Create document chunk in user's database"""
        return await self.model_ops.create_document(
            collection_name="document_chunks",
            model=chunk,
            user_id=user_id,
            operation_type="user",
            user_connection=user_connection
        )
    
    async def get_document_chunks(self, document_id: str, user_id: str, user_connection: str) -> list[DocumentChunk]:
        """Get all chunks for a document from user's database"""
        return await self.model_ops.find_documents(
            collection_name="document_chunks",
            filter_dict={"document_id": document_id},
            model_class=DocumentChunk,
            sort=[("chunk_index", 1)],
            user_id=user_id,
            operation_type="user",
            user_connection=user_connection
        )
    
    async def get_chat_chunks(self, chat_id: str, user_id: str, user_connection: str) -> list[DocumentChunk]:
        """Get all chunks for a chat from user's database"""
        return await self.model_ops.find_documents(
            collection_name="document_chunks",
            filter_dict={"chat_id": chat_id},
            model_class=DocumentChunk,
            sort=[("chunk_index", 1)],
            user_id=user_id,
            operation_type="user",
            user_connection=user_connection
        )
    
    # Utility Methods
    
    async def validate_user_database_access(self, user_id: str, user_connection: str) -> Dict[str, Any]:
        """Validate that user can access their database"""
        return await db_manager.test_user_database_operations(user_id, user_connection)
    
    async def get_user_with_connection(self, user_id: str) -> tuple[Optional[User], Optional[str]]:
        """Get user and their database connection string"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None, None
        
        connection = user.user_mongodb_connection
        if not connection:
            logger.warning(f"User {user_id} has no database connection configured")
        
        return user, connection
    
    async def ensure_user_database_setup(self, user_id: str, user_connection: str) -> bool:
        """Ensure user's database is properly set up with indexes"""
        try:
            # This will create indexes if they don't exist
            await db_manager.get_user_database(user_id, user_connection)
            return True
        except Exception as e:
            logger.error(f"Failed to set up user database for {user_id}: {e}")
            return False


# Global database router instance
db_router = DatabaseRouter()