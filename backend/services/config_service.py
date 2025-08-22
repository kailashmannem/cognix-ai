"""Configuration service for managing user API keys and database settings"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
import logging

from models.user import User, UserConfig
from utils.database import get_platform_database, db_manager
from utils.encryption import encryption_service
from utils.validators import validator
from services.auth_service import AuthService

logger = logging.getLogger(__name__)


class ConfigService:
    """Service class for user configuration management"""
    
    def __init__(self):
        self.auth_service = AuthService()
    
    async def update_user_config(self, user_id: str, config: UserConfig) -> Dict[str, Any]:
        """Update user configuration with validation and encryption"""
        db = get_platform_database()
        if not db:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not available"
            )
        
        update_data = {"updated_at": datetime.utcnow()}
        validation_results = {}
        
        # Handle API keys update
        if config.api_keys is not None:
            validated_keys = {}
            key_validation_results = {}
            
            for provider, api_key in config.api_keys.items():
                # Validate API key format
                is_valid, error_msg = validator.validate_api_key_format(provider, api_key)
                if not is_valid:
                    key_validation_results[provider] = {"valid": False, "error": error_msg}
                    continue
                
                # Test API key with provider (if possible)
                try:
                    key_test_result = await self._test_api_key(provider, api_key)
                    key_validation_results[provider] = key_test_result
                    
                    if key_test_result.get("valid", False):
                        # Encrypt and store valid API key
                        encrypted_key = encryption_service.encrypt(api_key)
                        validated_keys[provider] = encrypted_key
                except Exception as e:
                    logger.warning(f"Could not test API key for {provider}: {e}")
                    # Store key anyway if format is valid (testing might fail due to network issues)
                    encrypted_key = encryption_service.encrypt(api_key)
                    validated_keys[provider] = encrypted_key
                    key_validation_results[provider] = {
                        "valid": True, 
                        "warning": "Could not test key, but format is valid"
                    }
            
            if validated_keys:
                # Get existing API keys and merge
                user = await self.auth_service.get_user_by_id(user_id)
                if user and user.api_keys:
                    existing_keys = user.api_keys.copy()
                    existing_keys.update(validated_keys)
                    update_data["api_keys"] = existing_keys
                else:
                    update_data["api_keys"] = validated_keys
            
            validation_results["api_keys"] = key_validation_results
        
        # Handle MongoDB connection update
        if config.user_mongodb_connection is not None:
            connection_validation = await self._validate_mongodb_connection(
                user_id, config.user_mongodb_connection
            )
            validation_results["mongodb_connection"] = connection_validation
            
            if connection_validation.get("valid", False):
                # Encrypt and store connection string
                encrypted_connection = encryption_service.encrypt(config.user_mongodb_connection)
                update_data["user_mongodb_connection"] = encrypted_connection
                
                # Initialize user database schema
                try:
                    await self._initialize_user_database(user_id, config.user_mongodb_connection)
                    validation_results["database_initialization"] = {"success": True}
                except Exception as e:
                    logger.error(f"Failed to initialize user database: {e}")
                    validation_results["database_initialization"] = {
                        "success": False, 
                        "error": str(e)
                    }
        
        # Handle preferred LLM provider update
        if config.preferred_llm_provider is not None:
            if validator.validate_llm_provider(config.preferred_llm_provider):
                update_data["preferred_llm_provider"] = config.preferred_llm_provider
                validation_results["preferred_llm_provider"] = {"valid": True}
            else:
                validation_results["preferred_llm_provider"] = {
                    "valid": False, 
                    "error": "Invalid LLM provider"
                }
        
        # Update user in database
        try:
            from bson import ObjectId
            result = await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found or no changes made"
                )
            
            return {
                "success": True,
                "validation_results": validation_results,
                "updated_fields": list(update_data.keys())
            }
            
        except Exception as e:
            logger.error(f"Failed to update user config: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update configuration: {str(e)}"
            )
    
    async def get_user_config(self, user_id: str) -> Dict[str, Any]:
        """Get user configuration (with decrypted sensitive data)"""
        user = await self.auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Decrypt API keys
        decrypted_api_keys = {}
        if user.api_keys:
            for provider, encrypted_key in user.api_keys.items():
                try:
                    decrypted_key = encryption_service.decrypt(encrypted_key)
                    # Mask the key for security (show only first 8 and last 4 characters)
                    if len(decrypted_key) > 12:
                        masked_key = decrypted_key[:8] + "..." + decrypted_key[-4:]
                    else:
                        masked_key = "***"
                    decrypted_api_keys[provider] = {
                        "masked": masked_key,
                        "configured": True
                    }
                except Exception as e:
                    logger.error(f"Failed to decrypt API key for {provider}: {e}")
                    decrypted_api_keys[provider] = {
                        "masked": "***",
                        "configured": True,
                        "error": "Decryption failed"
                    }
        
        # Check MongoDB connection status
        mongodb_status = {"configured": False}
        if user.user_mongodb_connection:
            try:
                decrypted_connection = encryption_service.decrypt(user.user_mongodb_connection)
                # Test connection
                connection_test = await self._validate_mongodb_connection(user_id, decrypted_connection)
                mongodb_status = {
                    "configured": True,
                    "valid": connection_test.get("valid", False),
                    "database_name": connection_test.get("database_name"),
                    "error": connection_test.get("error")
                }
            except Exception as e:
                logger.error(f"Failed to check MongoDB connection: {e}")
                mongodb_status = {
                    "configured": True,
                    "valid": False,
                    "error": "Connection check failed"
                }
        
        return {
            "api_keys": decrypted_api_keys,
            "mongodb_connection": mongodb_status,
            "preferred_llm_provider": user.preferred_llm_provider,
            "updated_at": user.updated_at
        }
    
    async def get_user_api_key(self, user_id: str, provider: str) -> Optional[str]:
        """Get decrypted API key for a specific provider"""
        user = await self.auth_service.get_user_by_id(user_id)
        if not user or not user.api_keys or provider not in user.api_keys:
            return None
        
        try:
            encrypted_key = user.api_keys[provider]
            return encryption_service.decrypt(encrypted_key)
        except Exception as e:
            logger.error(f"Failed to decrypt API key for {provider}: {e}")
            return None
    
    async def get_user_mongodb_connection(self, user_id: str) -> Optional[str]:
        """Get decrypted MongoDB connection string"""
        user = await self.auth_service.get_user_by_id(user_id)
        if not user or not user.user_mongodb_connection:
            return None
        
        try:
            return encryption_service.decrypt(user.user_mongodb_connection)
        except Exception as e:
            logger.error(f"Failed to decrypt MongoDB connection: {e}")
            return None
    
    async def delete_api_key(self, user_id: str, provider: str) -> bool:
        """Delete API key for a specific provider"""
        db = get_platform_database()
        if not db:
            return False
        
        try:
            from bson import ObjectId
            result = await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$unset": {f"api_keys.{provider}": ""},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to delete API key for {provider}: {e}")
            return False
    
    async def test_user_database_connection(self, user_id: str) -> Dict[str, Any]:
        """Test user's current database connection"""
        connection_string = await self.get_user_mongodb_connection(user_id)
        if not connection_string:
            return {
                "success": False,
                "error": "No database connection configured"
            }
        
        return await self._validate_mongodb_connection(user_id, connection_string)
    
    async def _test_api_key(self, provider: str, api_key: str) -> Dict[str, Any]:
        """Test API key with the provider"""
        # This is a basic implementation - in a real system, you'd make actual API calls
        # to test the keys with each provider
        
        result = {"valid": True, "tested": False}
        
        try:
            if provider == "openai":
                # Test OpenAI API key
                import openai
                client = openai.AsyncOpenAI(api_key=api_key)
                # Make a simple API call to test the key
                await client.models.list()
                result["tested"] = True
                
            elif provider == "gemini":
                # Test Gemini API key
                # This would require Google AI SDK
                result["warning"] = "Gemini API key testing not implemented"
                
            elif provider == "groq":
                # Test Groq API key
                # This would require Groq SDK
                result["warning"] = "Groq API key testing not implemented"
                
            elif provider == "mistral":
                # Test Mistral API key
                # This would require Mistral SDK
                result["warning"] = "Mistral API key testing not implemented"
                
        except Exception as e:
            result["valid"] = False
            result["error"] = str(e)
        
        return result
    
    async def _validate_mongodb_connection(self, user_id: str, connection_string: str) -> Dict[str, Any]:
        """Validate MongoDB connection string and test operations"""
        try:
            # Use the database manager's validation method
            validation_result = await db_manager.validate_user_connection(connection_string)
            
            if validation_result["valid"]:
                # Test basic CRUD operations
                operations_test = await db_manager.test_user_database_operations(user_id, connection_string)
                validation_result.update(operations_test)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"MongoDB connection validation failed: {e}")
            return {
                "valid": False,
                "error": str(e)
            }
    
    async def _initialize_user_database(self, user_id: str, connection_string: str):
        """Initialize user's database with proper schema and indexes"""
        try:
            # This will create the connection and set up indexes
            await db_manager.get_user_database(user_id, connection_string)
            logger.info(f"Successfully initialized database for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database for user {user_id}: {e}")
            raise
    
    async def validate_all_user_configs(self, user_id: str) -> Dict[str, Any]:
        """Validate all user configurations (API keys, database connection)"""
        results = {
            "user_id": user_id,
            "api_keys": {},
            "mongodb_connection": {},
            "overall_status": "unknown"
        }
        
        user = await self.auth_service.get_user_by_id(user_id)
        if not user:
            results["overall_status"] = "error"
            results["error"] = "User not found"
            return results
        
        # Validate API keys
        if user.api_keys:
            for provider, encrypted_key in user.api_keys.items():
                try:
                    decrypted_key = encryption_service.decrypt(encrypted_key)
                    key_result = await self._test_api_key(provider, decrypted_key)
                    results["api_keys"][provider] = key_result
                except Exception as e:
                    results["api_keys"][provider] = {
                        "valid": False,
                        "error": f"Decryption or testing failed: {str(e)}"
                    }
        
        # Validate MongoDB connection
        if user.user_mongodb_connection:
            try:
                decrypted_connection = encryption_service.decrypt(user.user_mongodb_connection)
                connection_result = await self._validate_mongodb_connection(user_id, decrypted_connection)
                results["mongodb_connection"] = connection_result
            except Exception as e:
                results["mongodb_connection"] = {
                    "valid": False,
                    "error": f"Connection validation failed: {str(e)}"
                }
        
        # Determine overall status
        api_keys_valid = all(
            result.get("valid", False) 
            for result in results["api_keys"].values()
        ) if results["api_keys"] else True
        
        mongodb_valid = results["mongodb_connection"].get("valid", True)
        
        if api_keys_valid and mongodb_valid:
            results["overall_status"] = "valid"
        elif not api_keys_valid or not mongodb_valid:
            results["overall_status"] = "invalid"
        else:
            results["overall_status"] = "partial"
        
        return results


# Global config service instance
config_service = ConfigService()