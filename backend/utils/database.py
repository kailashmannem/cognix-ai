"""Database connection utilities for MongoDB"""

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, Any
import logging
import asyncio
from urllib.parse import urlparse

from utils.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        self.platform_client: Optional[AsyncIOMotorClient] = None
        self.platform_db = None
        self.user_clients = {}  # Cache for user database connections
        self._platform_indexes_created = False

    async def connect_to_platform_db(self):
        """Connect to the platform database for user authentication"""
        try:
            self.platform_client = AsyncIOMotorClient(settings.PLATFORM_MONGODB_URL)
            self.platform_db = self.platform_client[settings.PLATFORM_DATABASE_NAME]
            
            # Test the connection
            await self.platform_client.admin.command('ping')
            logger.info("Connected to platform MongoDB database")
            
            # Create indexes for platform database
            await self._create_platform_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to platform database: {e}")
            raise

    async def _create_platform_indexes(self):
        """Create indexes for platform database collections"""
        if self._platform_indexes_created:
            return
            
        try:
            # Users collection indexes
            users_collection = self.platform_db.users
            await users_collection.create_index("email", unique=True)
            await users_collection.create_index("created_at")
            
            logger.info("Created platform database indexes")
            self._platform_indexes_created = True
            
        except Exception as e:
            logger.error(f"Failed to create platform indexes: {e}")
            # Don't raise - indexes might already exist

    async def get_user_database(self, user_id: str, connection_string: str):
        """Get or create connection to user's personal database"""
        try:
            if user_id not in self.user_clients:
                client = AsyncIOMotorClient(connection_string)
                # Test the connection
                await client.admin.command('ping')
                self.user_clients[user_id] = {
                    'client': client,
                    'indexes_created': False
                }
                logger.info(f"Connected to user database for user {user_id}")
            
            # Extract database name from connection string or use default
            db_name = self._extract_database_name(connection_string, user_id)
            user_db = self.user_clients[user_id]['client'][db_name]
            
            # Create indexes for user database if not already created
            if not self.user_clients[user_id]['indexes_created']:
                await self._create_user_database_indexes(user_db)
                self.user_clients[user_id]['indexes_created'] = True
            
            return user_db
            
        except Exception as e:
            logger.error(f"Failed to connect to user database: {e}")
            raise

    def _extract_database_name(self, connection_string: str, user_id: str) -> str:
        """Extract database name from connection string or generate default"""
        try:
            parsed = urlparse(connection_string)
            if parsed.path and len(parsed.path) > 1:
                return parsed.path[1:]  # Remove leading slash
            else:
                return f"cognix_user_{user_id}"
        except Exception:
            return f"cognix_user_{user_id}"

    async def _create_user_database_indexes(self, user_db):
        """Create indexes for user database collections"""
        try:
            # Chat sessions collection indexes
            chat_sessions = user_db.chat_sessions
            await chat_sessions.create_index("user_id")
            await chat_sessions.create_index("created_at")
            await chat_sessions.create_index([("user_id", 1), ("created_at", -1)])
            
            # Messages collection indexes
            messages = user_db.messages
            await messages.create_index("chat_id")
            await messages.create_index("timestamp")
            await messages.create_index([("chat_id", 1), ("timestamp", 1)])
            
            # Documents collection indexes
            documents = user_db.documents
            await documents.create_index("chat_id")
            await documents.create_index("upload_date")
            await documents.create_index("processing_status")
            
            # Document chunks collection indexes
            document_chunks = user_db.document_chunks
            await document_chunks.create_index("document_id")
            await document_chunks.create_index("chat_id")
            await document_chunks.create_index([("document_id", 1), ("chunk_index", 1)])
            await document_chunks.create_index([("chat_id", 1), ("chunk_index", 1)])
            
            logger.info("Created user database indexes")
            
        except Exception as e:
            logger.error(f"Failed to create user database indexes: {e}")
            # Don't raise - indexes might already exist

    async def close_user_connection(self, user_id: str):
        """Close connection to user's database"""
        if user_id in self.user_clients:
            self.user_clients[user_id]['client'].close()
            del self.user_clients[user_id]
            logger.info(f"Closed user database connection for user {user_id}")

    async def close_all_connections(self):
        """Close all database connections"""
        if self.platform_client:
            self.platform_client.close()
            logger.info("Closed platform database connection")
        
        for user_id, client_info in self.user_clients.items():
            client_info['client'].close()
            logger.info(f"Closed user database connection for user {user_id}")
        
        self.user_clients.clear()

    async def validate_user_connection(self, connection_string: str) -> Dict[str, Any]:
        """Validate user's MongoDB connection string and return detailed info"""
        result = {
            'valid': False,
            'error': None,
            'database_name': None,
            'server_info': None
        }
        
        test_client = None
        try:
            test_client = AsyncIOMotorClient(connection_string, serverSelectionTimeoutMS=5000)
            
            # Test basic connectivity
            await test_client.admin.command('ping')
            
            # Get server information
            server_info = await test_client.admin.command('buildInfo')
            result['server_info'] = {
                'version': server_info.get('version'),
                'maxBsonObjectSize': server_info.get('maxBsonObjectSize')
            }
            
            # Extract database name
            result['database_name'] = self._extract_database_name(connection_string, 'test')
            
            # Test database access
            test_db = test_client[result['database_name']]
            await test_db.command('ping')
            
            result['valid'] = True
            logger.info("User connection string validated successfully")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Invalid user connection string: {e}")
        finally:
            if test_client:
                test_client.close()
        
        return result

    async def test_user_database_operations(self, user_id: str, connection_string: str) -> Dict[str, Any]:
        """Test basic CRUD operations on user's database"""
        result = {
            'success': False,
            'operations_tested': [],
            'error': None
        }
        
        test_client = None
        try:
            test_client = AsyncIOMotorClient(connection_string, serverSelectionTimeoutMS=5000)
            db_name = self._extract_database_name(connection_string, user_id)
            test_db = test_client[db_name]
            test_collection = test_db.test_collection
            
            # Test insert
            test_doc = {'test': True, 'user_id': user_id}
            insert_result = await test_collection.insert_one(test_doc)
            result['operations_tested'].append('insert')
            
            # Test find
            found_doc = await test_collection.find_one({'_id': insert_result.inserted_id})
            if not found_doc:
                raise Exception("Document not found after insert")
            result['operations_tested'].append('find')
            
            # Test update
            await test_collection.update_one(
                {'_id': insert_result.inserted_id},
                {'$set': {'updated': True}}
            )
            result['operations_tested'].append('update')
            
            # Test delete
            await test_collection.delete_one({'_id': insert_result.inserted_id})
            result['operations_tested'].append('delete')
            
            # Clean up test collection
            await test_collection.drop()
            
            result['success'] = True
            logger.info(f"User database operations test successful for user {user_id}")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"User database operations test failed: {e}")
        finally:
            if test_client:
                test_client.close()
        
        return result

    def route_to_database(self, user_id: str = None, operation_type: str = "user") -> str:
        """Determine which database to use based on operation type"""
        if operation_type == "platform" or operation_type == "auth":
            return "platform"
        elif operation_type == "user" and user_id:
            return "user"
        else:
            raise ValueError(f"Invalid operation type or missing user_id: {operation_type}, {user_id}")

    async def get_database_for_operation(self, user_id: str = None, operation_type: str = "user", user_connection: str = None):
        """Get the appropriate database instance based on operation type"""
        route = self.route_to_database(user_id, operation_type)
        
        if route == "platform":
            if not self.platform_db:
                raise Exception("Platform database not connected")
            return self.platform_db
        elif route == "user":
            if not user_connection:
                raise ValueError("User connection string required for user operations")
            return await self.get_user_database(user_id, user_connection)
        else:
            raise ValueError(f"Unknown database route: {route}")


# Global database manager instance
db_manager = DatabaseManager()


async def connect_to_mongo():
    """Initialize database connections"""
    await db_manager.connect_to_platform_db()


async def close_mongo_connection():
    """Close all database connections"""
    await db_manager.close_all_connections()


def get_platform_database():
    """Get platform database instance"""
    return db_manager.platform_db


async def get_user_database(user_id: str, connection_string: str):
    """Get user's personal database instance"""
    return await db_manager.get_user_database(user_id, connection_string)


async def validate_user_connection_string(connection_string: str):
    """Validate user's MongoDB connection string"""
    return await db_manager.validate_user_connection(connection_string)


async def test_user_database_operations(user_id: str, connection_string: str):
    """Test basic CRUD operations on user's database"""
    return await db_manager.test_user_database_operations(user_id, connection_string)