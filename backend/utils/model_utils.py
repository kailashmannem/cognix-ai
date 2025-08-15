"""Model validation and serialization utilities"""

from typing import Dict, Any, List, Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class ModelValidator:
    """Utility class for model validation and serialization"""
    
    @staticmethod
    def validate_model(model_class: Type[T], data: Dict[str, Any]) -> T:
        """Validate data against a Pydantic model"""
        try:
            return model_class(**data)
        except ValidationError as e:
            logger.error(f"Model validation failed for {model_class.__name__}: {e}")
            raise ValueError(f"Invalid data for {model_class.__name__}: {e}")
    
    @staticmethod
    def serialize_for_mongo(model: BaseModel) -> Dict[str, Any]:
        """Serialize Pydantic model for MongoDB storage"""
        data = model.dict(by_alias=True, exclude_unset=True)
        
        # Handle ObjectId serialization
        for key, value in data.items():
            if isinstance(value, ObjectId):
                data[key] = value
            elif key == '_id' and isinstance(value, str):
                try:
                    data[key] = ObjectId(value)
                except Exception:
                    pass  # Keep as string if not valid ObjectId
        
        return data
    
    @staticmethod
    def deserialize_from_mongo(model_class: Type[T], data: Dict[str, Any]) -> T:
        """Deserialize MongoDB document to Pydantic model"""
        if not data:
            return None
        
        # Handle ObjectId deserialization
        if '_id' in data and isinstance(data['_id'], ObjectId):
            data['_id'] = str(data['_id'])
        
        try:
            return model_class(**data)
        except ValidationError as e:
            logger.error(f"Deserialization failed for {model_class.__name__}: {e}")
            raise ValueError(f"Invalid MongoDB data for {model_class.__name__}: {e}")
    
    @staticmethod
    def serialize_list_for_mongo(models: List[BaseModel]) -> List[Dict[str, Any]]:
        """Serialize list of Pydantic models for MongoDB storage"""
        return [ModelValidator.serialize_for_mongo(model) for model in models]
    
    @staticmethod
    def deserialize_list_from_mongo(model_class: Type[T], data_list: List[Dict[str, Any]]) -> List[T]:
        """Deserialize list of MongoDB documents to Pydantic models"""
        return [ModelValidator.deserialize_from_mongo(model_class, data) for data in data_list if data]
    
    @staticmethod
    def validate_object_id(id_str: str) -> bool:
        """Validate if string is a valid ObjectId"""
        try:
            ObjectId(id_str)
            return True
        except Exception:
            return False
    
    @staticmethod
    def ensure_object_id(id_value: Any) -> ObjectId:
        """Ensure value is an ObjectId"""
        if isinstance(id_value, ObjectId):
            return id_value
        elif isinstance(id_value, str):
            try:
                return ObjectId(id_value)
            except Exception:
                raise ValueError(f"Invalid ObjectId string: {id_value}")
        else:
            raise ValueError(f"Cannot convert {type(id_value)} to ObjectId")


class ModelOperations:
    """Database operations for models with validation"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.validator = ModelValidator()
    
    async def create_document(self, collection_name: str, model: BaseModel, 
                            user_id: str = None, operation_type: str = "user",
                            user_connection: str = None) -> str:
        """Create a document in the appropriate database"""
        try:
            db = await self.db_manager.get_database_for_operation(
                user_id=user_id, 
                operation_type=operation_type, 
                user_connection=user_connection
            )
            
            collection = db[collection_name]
            document_data = self.validator.serialize_for_mongo(model)
            
            result = await collection.insert_one(document_data)
            logger.info(f"Created document in {collection_name}: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to create document in {collection_name}: {e}")
            raise
    
    async def get_document(self, collection_name: str, document_id: str, model_class: Type[T],
                          user_id: str = None, operation_type: str = "user",
                          user_connection: str = None) -> Optional[T]:
        """Get a document from the appropriate database"""
        try:
            db = await self.db_manager.get_database_for_operation(
                user_id=user_id, 
                operation_type=operation_type, 
                user_connection=user_connection
            )
            
            collection = db[collection_name]
            object_id = self.validator.ensure_object_id(document_id)
            
            document_data = await collection.find_one({"_id": object_id})
            if not document_data:
                return None
            
            return self.validator.deserialize_from_mongo(model_class, document_data)
            
        except Exception as e:
            logger.error(f"Failed to get document from {collection_name}: {e}")
            raise
    
    async def update_document(self, collection_name: str, document_id: str, 
                            update_data: Dict[str, Any],
                            user_id: str = None, operation_type: str = "user",
                            user_connection: str = None) -> bool:
        """Update a document in the appropriate database"""
        try:
            db = await self.db_manager.get_database_for_operation(
                user_id=user_id, 
                operation_type=operation_type, 
                user_connection=user_connection
            )
            
            collection = db[collection_name]
            object_id = self.validator.ensure_object_id(document_id)
            
            result = await collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Updated document in {collection_name}: {document_id}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to update document in {collection_name}: {e}")
            raise
    
    async def delete_document(self, collection_name: str, document_id: str,
                            user_id: str = None, operation_type: str = "user",
                            user_connection: str = None) -> bool:
        """Delete a document from the appropriate database"""
        try:
            db = await self.db_manager.get_database_for_operation(
                user_id=user_id, 
                operation_type=operation_type, 
                user_connection=user_connection
            )
            
            collection = db[collection_name]
            object_id = self.validator.ensure_object_id(document_id)
            
            result = await collection.delete_one({"_id": object_id})
            
            success = result.deleted_count > 0
            if success:
                logger.info(f"Deleted document from {collection_name}: {document_id}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete document from {collection_name}: {e}")
            raise
    
    async def find_documents(self, collection_name: str, filter_dict: Dict[str, Any], 
                           model_class: Type[T], limit: int = None, skip: int = None,
                           sort: List[tuple] = None,
                           user_id: str = None, operation_type: str = "user",
                           user_connection: str = None) -> List[T]:
        """Find documents in the appropriate database"""
        try:
            db = await self.db_manager.get_database_for_operation(
                user_id=user_id, 
                operation_type=operation_type, 
                user_connection=user_connection
            )
            
            collection = db[collection_name]
            cursor = collection.find(filter_dict)
            
            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
            
            documents = await cursor.to_list(length=limit)
            return self.validator.deserialize_list_from_mongo(model_class, documents)
            
        except Exception as e:
            logger.error(f"Failed to find documents in {collection_name}: {e}")
            raise