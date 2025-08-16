"""Authentication service for user registration, login, and token verification"""

from typing import Optional
from datetime import datetime
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from models.user import User, UserCreate, UserLogin, UserResponse, UserValidation
from utils.auth import PasswordUtils, JWTUtils, TokenData
from utils.database import get_platform_database
from utils.encryption import encrypt_data, decrypt_data


class AuthService:
    """Service class for authentication operations"""
    
    def __init__(self):
        self.password_utils = PasswordUtils()
        self.jwt_utils = JWTUtils()
    
    async def register_user(self, user_data: UserCreate) -> UserResponse:
        """Register a new user"""
        db = await get_platform_database()
        
        # Validate email format
        if not UserValidation.validate_email_format(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        # Validate password strength
        if not UserValidation.validate_password_strength(user_data.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long and contain uppercase, lowercase, and numeric characters"
            )
        
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data.email.lower()})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        password_hash = self.password_utils.hash_password(user_data.password)
        
        # Create user document
        user_doc = {
            "email": user_data.email.lower(),
            "password_hash": password_hash,
            "api_keys": {},
            "user_mongodb_connection": None,
            "preferred_llm_provider": "openai",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Sanitize user data
        user_doc = UserValidation.sanitize_user_data(user_doc)
        
        # Insert user into database
        result = await db.users.insert_one(user_doc)
        
        # Fetch the created user
        created_user = await db.users.find_one({"_id": result.inserted_id})
        
        return UserResponse(
            id=str(created_user["_id"]),
            email=created_user["email"],
            preferred_llm_provider=created_user["preferred_llm_provider"],
            created_at=created_user["created_at"],
            updated_at=created_user["updated_at"]
        )
    
    async def authenticate_user(self, login_data: UserLogin) -> str:
        """Authenticate user and return JWT token"""
        db = await get_platform_database()
        
        # Find user by email
        user = await db.users.find_one({"email": login_data.email.lower()})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not self.password_utils.verify_password(login_data.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create JWT token
        access_token = self.jwt_utils.create_token_for_user(
            user_id=str(user["_id"]),
            email=user["email"]
        )
        
        return access_token
    
    async def verify_token(self, token: str) -> User:
        """Verify JWT token and return user"""
        # Decode token
        token_data = self.jwt_utils.verify_token(token)
        
        # Get user from database
        db = await get_platform_database()
        user = await db.users.find_one({"_id": ObjectId(token_data.user_id)})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return User(**user)
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        db = await get_platform_database()
        
        try:
            user = await db.users.find_one({"_id": ObjectId(user_id)})
            if user:
                return User(**user)
            return None
        except Exception:
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        db = await get_platform_database()
        
        user = await db.users.find_one({"email": email.lower()})
        if user:
            return User(**user)
        return None
    
    async def update_user_api_keys(self, user_id: str, provider: str, api_key: str) -> bool:
        """Update user's API keys (encrypted)"""
        db = await get_platform_database()
        
        # Encrypt the API key
        encrypted_key = encrypt_data(api_key)
        
        # Update user's API keys
        result = await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    f"api_keys.{provider}": encrypted_key,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    async def get_user_api_key(self, user_id: str, provider: str) -> Optional[str]:
        """Get user's API key for a provider (decrypted)"""
        db = await get_platform_database()
        
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user or "api_keys" not in user or provider not in user["api_keys"]:
            return None
        
        # Decrypt the API key
        encrypted_key = user["api_keys"][provider]
        try:
            decrypted_key = decrypt_data(encrypted_key)
            return decrypted_key
        except Exception:
            return None
    
    async def update_user_mongodb_connection(self, user_id: str, connection_string: str) -> bool:
        """Update user's MongoDB connection string (encrypted)"""
        db = await get_platform_database()
        
        # Encrypt the connection string
        encrypted_connection = encrypt_data(connection_string)
        
        # Update user's MongoDB connection
        result = await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "user_mongodb_connection": encrypted_connection,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    async def get_user_mongodb_connection(self, user_id: str) -> Optional[str]:
        """Get user's MongoDB connection string (decrypted)"""
        db = await get_platform_database()
        
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user or not user.get("user_mongodb_connection"):
            return None
        
        # Decrypt the connection string
        encrypted_connection = user["user_mongodb_connection"]
        try:
            decrypted_connection = decrypt_data(encrypted_connection)
            return decrypted_connection
        except Exception:
            return None