"""Chat service for managing chat sessions and messages"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from models.chat import ChatSession, Message, ChatSessionCreate, MessageCreateValidated
from models.user import User
from utils.database_router import db_router

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self):
        self.db_router = db_router

    async def create_chat_session(self, user_id: str, user_connection: str, title: str = None) -> ChatSession:
        """Create a new chat session in user's database"""
        try:
            # Generate default title if not provided
            if not title:
                title = f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
            
            # Validate title
            chat_create = ChatSessionCreate(title=title)
            
            # Create chat session model
            chat_session = ChatSession(
                user_id=user_id,
                title=chat_create.title,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Store in user's database
            chat_id = await self.db_router.create_chat_session(
                chat_session=chat_session,
                user_id=user_id,
                user_connection=user_connection
            )
            
            # Update the chat session with the generated ID
            chat_session.id = chat_id
            
            logger.info(f"Created chat session {chat_id} for user {user_id}")
            return chat_session
            
        except Exception as e:
            logger.error(f"Failed to create chat session for user {user_id}: {e}")
            raise

    async def get_user_chats(self, user_id: str, user_connection: str, limit: int = None) -> List[ChatSession]:
        """Get all chat sessions for a user from their database"""
        try:
            chats = await self.db_router.get_user_chat_sessions(
                user_id=user_id,
                user_connection=user_connection,
                limit=limit
            )
            
            logger.info(f"Retrieved {len(chats)} chat sessions for user {user_id}")
            return chats
            
        except Exception as e:
            logger.error(f"Failed to get chat sessions for user {user_id}: {e}")
            raise

    async def get_chat_session(self, chat_id: str, user_id: str, user_connection: str) -> Optional[ChatSession]:
        """Get a specific chat session from user's database"""
        try:
            chat = await self.db_router.get_chat_session(
                chat_id=chat_id,
                user_id=user_id,
                user_connection=user_connection
            )
            
            if chat:
                logger.info(f"Retrieved chat session {chat_id} for user {user_id}")
            else:
                logger.warning(f"Chat session {chat_id} not found for user {user_id}")
            
            return chat
            
        except Exception as e:
            logger.error(f"Failed to get chat session {chat_id} for user {user_id}: {e}")
            raise

    async def get_chat_messages(self, chat_id: str, user_id: str, user_connection: str, 
                              limit: int = None, skip: int = None) -> List[Message]:
        """Get all messages for a chat session from user's database"""
        try:
            # First verify the chat exists and belongs to the user
            chat = await self.get_chat_session(chat_id, user_id, user_connection)
            if not chat:
                raise ValueError(f"Chat session {chat_id} not found or access denied")
            
            messages = await self.db_router.get_chat_messages(
                chat_id=chat_id,
                user_id=user_id,
                user_connection=user_connection,
                limit=limit,
                skip=skip
            )
            
            logger.info(f"Retrieved {len(messages)} messages for chat {chat_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get messages for chat {chat_id}: {e}")
            raise

    async def send_message(self, chat_id: str, user_id: str, user_connection: str, 
                          content: str, role: str = "user", context_used: Optional[List[str]] = None) -> Message:
        """Send a message in a chat session to user's database"""
        try:
            # First verify the chat exists and belongs to the user
            chat = await self.get_chat_session(chat_id, user_id, user_connection)
            if not chat:
                raise ValueError(f"Chat session {chat_id} not found or access denied")
            
            # Validate message content
            message_create = MessageCreateValidated(content=content, role=role)
            
            # Create message model
            message = Message(
                chat_id=chat_id,
                content=message_create.content,
                role=message_create.role,
                timestamp=datetime.utcnow(),
                context_used=context_used
            )
            
            # Store in user's database
            message_id = await self.db_router.create_message(
                message=message,
                user_id=user_id,
                user_connection=user_connection
            )
            
            # Update the message with the generated ID
            message.id = message_id
            
            # Update chat session's updated_at timestamp
            await self.update_chat_session(
                chat_id=chat_id,
                user_id=user_id,
                user_connection=user_connection,
                update_data={"updated_at": datetime.utcnow()}
            )
            
            logger.info(f"Sent message {message_id} to chat {chat_id}")
            return message
            
        except Exception as e:
            logger.error(f"Failed to send message to chat {chat_id}: {e}")
            raise

    async def update_chat_session(self, chat_id: str, user_id: str, user_connection: str, 
                                update_data: Dict[str, Any]) -> bool:
        """Update a chat session in user's database"""
        try:
            # First verify the chat exists and belongs to the user
            chat = await self.get_chat_session(chat_id, user_id, user_connection)
            if not chat:
                raise ValueError(f"Chat session {chat_id} not found or access denied")
            
            # Add updated_at timestamp
            update_data["updated_at"] = datetime.utcnow()
            
            success = await self.db_router.update_chat_session(
                chat_id=chat_id,
                update_data=update_data,
                user_id=user_id,
                user_connection=user_connection
            )
            
            if success:
                logger.info(f"Updated chat session {chat_id}")
            else:
                logger.warning(f"Failed to update chat session {chat_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update chat session {chat_id}: {e}")
            raise

    async def delete_chat_session(self, chat_id: str, user_id: str, user_connection: str) -> bool:
        """Delete a chat session and all associated data from user's database"""
        try:
            # First verify the chat exists and belongs to the user
            chat = await self.get_chat_session(chat_id, user_id, user_connection)
            if not chat:
                raise ValueError(f"Chat session {chat_id} not found or access denied")
            
            # Delete chat session and all related data (messages, documents, chunks)
            success = await self.db_router.delete_chat_session(
                chat_id=chat_id,
                user_id=user_id,
                user_connection=user_connection
            )
            
            if success:
                logger.info(f"Deleted chat session {chat_id} and all associated data")
            else:
                logger.warning(f"Failed to delete chat session {chat_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete chat session {chat_id}: {e}")
            raise

    async def validate_user_access_to_chat(self, chat_id: str, user_id: str, user_connection: str) -> bool:
        """Validate that a user has access to a specific chat session"""
        try:
            chat = await self.get_chat_session(chat_id, user_id, user_connection)
            return chat is not None and chat.user_id == user_id
        except Exception:
            return False

    async def get_chat_statistics(self, user_id: str, user_connection: str) -> Dict[str, Any]:
        """Get statistics about user's chats"""
        try:
            chats = await self.get_user_chats(user_id, user_connection)
            
            total_chats = len(chats)
            chats_with_documents = len([chat for chat in chats if chat.document_name])
            
            # Get total message count across all chats
            total_messages = 0
            for chat in chats:
                messages = await self.get_chat_messages(str(chat.id), user_id, user_connection)
                total_messages += len(messages)
            
            return {
                "total_chats": total_chats,
                "chats_with_documents": chats_with_documents,
                "total_messages": total_messages,
                "average_messages_per_chat": total_messages / total_chats if total_chats > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get chat statistics for user {user_id}: {e}")
            raise


# Global chat service instance
chat_service = ChatService()