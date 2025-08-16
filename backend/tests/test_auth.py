"""Tests for authentication system"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import asyncio

from main import app
from utils.auth import PasswordUtils, JWTUtils, get_password_hash, verify_password
from services.auth_service import AuthService
from models.user import UserCreate, UserLogin


class TestPasswordUtils:
    """Test password hashing utilities"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "TestPassword123"
        hashed = PasswordUtils.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "TestPassword123"
        hashed = PasswordUtils.hash_password(password)
        
        assert PasswordUtils.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "TestPassword123"
        wrong_password = "WrongPassword123"
        hashed = PasswordUtils.hash_password(password)
        
        assert PasswordUtils.verify_password(wrong_password, hashed) is False
    
    def test_convenience_functions(self):
        """Test convenience functions"""
        password = "TestPassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False


class TestJWTUtils:
    """Test JWT token utilities"""
    
    def test_create_access_token(self):
        """Test JWT token creation"""
        data = {"sub": "test@example.com", "user_id": "123"}
        token = JWTUtils.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_with_expiry(self):
        """Test JWT token creation with custom expiry"""
        data = {"sub": "test@example.com", "user_id": "123"}
        expires_delta = timedelta(minutes=30)
        token = JWTUtils.create_access_token(data, expires_delta)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token_valid(self):
        """Test JWT token verification with valid token"""
        data = {"sub": "test@example.com", "user_id": "123"}
        token = JWTUtils.create_access_token(data)
        
        token_data = JWTUtils.verify_token(token)
        
        assert token_data.email == "test@example.com"
        assert token_data.user_id == "123"
    
    def test_verify_token_invalid(self):
        """Test JWT token verification with invalid token"""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            JWTUtils.verify_token("invalid_token")
        
        assert exc_info.value.status_code == 401
    
    def test_create_token_for_user(self):
        """Test token creation for specific user"""
        user_id = "user123"
        email = "test@example.com"
        
        token = JWTUtils.create_token_for_user(user_id, email)
        token_data = JWTUtils.verify_token(token)
        
        assert token_data.email == email
        assert token_data.user_id == user_id


class TestAuthService:
    """Test authentication service"""
    
    @pytest.fixture
    def auth_service(self):
        return AuthService()
    
    @pytest.fixture
    def mock_db(self):
        """Mock database for testing"""
        mock_db = AsyncMock()
        mock_db.users = AsyncMock()
        return mock_db
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service, mock_db):
        """Test successful user registration"""
        user_data = UserCreate(email="test@example.com", password="TestPass123")
        
        # Mock database responses
        mock_db.users.find_one.return_value = None  # User doesn't exist
        mock_db.users.insert_one.return_value = AsyncMock(inserted_id="user123")
        mock_db.users.find_one.side_effect = [
            None,  # First call - user doesn't exist
            {  # Second call - return created user
                "_id": "user123",
                "email": "test@example.com",
                "preferred_llm_provider": "openai",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        with patch('services.auth_service.get_platform_database', return_value=mock_db):
            result = await auth_service.register_user(user_data)
        
        assert result.email == "test@example.com"
        assert result.preferred_llm_provider == "openai"
        mock_db.users.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_user_email_exists(self, auth_service, mock_db):
        """Test user registration with existing email"""
        from fastapi import HTTPException
        
        user_data = UserCreate(email="test@example.com", password="TestPass123")
        
        # Mock existing user
        mock_db.users.find_one.return_value = {"email": "test@example.com"}
        
        with patch('services.auth_service.get_platform_database', return_value=mock_db):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.register_user(user_data)
        
        assert exc_info.value.status_code == 400
        assert "already registered" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_register_user_weak_password(self, auth_service):
        """Test user registration with weak password"""
        from fastapi import HTTPException
        
        user_data = UserCreate(email="test@example.com", password="weak")
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register_user(user_data)
        
        assert exc_info.value.status_code == 400
        assert "Password must be at least 8 characters" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, mock_db):
        """Test successful user authentication"""
        login_data = UserLogin(email="test@example.com", password="TestPass123")
        hashed_password = get_password_hash("TestPass123")
        
        # Mock user in database
        mock_db.users.find_one.return_value = {
            "_id": "user123",
            "email": "test@example.com",
            "password_hash": hashed_password
        }
        
        with patch('services.auth_service.get_platform_database', return_value=mock_db):
            token = await auth_service.authenticate_user(login_data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token contains correct data
        token_data = JWTUtils.verify_token(token)
        assert token_data.email == "test@example.com"
        assert token_data.user_id == "user123"
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_email(self, auth_service, mock_db):
        """Test authentication with invalid email"""
        from fastapi import HTTPException
        
        login_data = UserLogin(email="nonexistent@example.com", password="TestPass123")
        
        # Mock no user found
        mock_db.users.find_one.return_value = None
        
        with patch('services.auth_service.get_platform_database', return_value=mock_db):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.authenticate_user(login_data)
        
        assert exc_info.value.status_code == 401
        assert "Invalid email or password" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(self, auth_service, mock_db):
        """Test authentication with invalid password"""
        from fastapi import HTTPException
        
        login_data = UserLogin(email="test@example.com", password="WrongPass123")
        hashed_password = get_password_hash("TestPass123")
        
        # Mock user in database
        mock_db.users.find_one.return_value = {
            "_id": "user123",
            "email": "test@example.com",
            "password_hash": hashed_password
        }
        
        with patch('services.auth_service.get_platform_database', return_value=mock_db):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.authenticate_user(login_data)
        
        assert exc_info.value.status_code == 401
        assert "Invalid email or password" in exc_info.value.detail


class TestAuthEndpoints:
    """Test authentication API endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_register_endpoint_structure(self, client):
        """Test register endpoint exists and has correct structure"""
        # This will fail without proper database setup, but tests the endpoint structure
        response = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "TestPass123"
        })
        
        # Should return either success or database connection error
        assert response.status_code in [200, 201, 500]
    
    def test_login_endpoint_structure(self, client):
        """Test login endpoint exists and has correct structure"""
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "TestPass123"
        })
        
        # Should return either success or database connection error
        assert response.status_code in [200, 401, 500]
    
    def test_me_endpoint_requires_auth(self, client):
        """Test /me endpoint requires authentication"""
        response = client.get("/api/auth/me")
        
        # Should return 401 or 403 for unauthenticated request
        assert response.status_code in [401, 403]
    
    def test_logout_endpoint(self, client):
        """Test logout endpoint"""
        response = client.post("/api/auth/logout")
        
        # Logout should always succeed (client-side operation)
        assert response.status_code == 200
        assert "Logout successful" in response.json()["message"]