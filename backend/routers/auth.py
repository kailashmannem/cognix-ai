from fastapi import APIRouter, HTTPException, status, Depends
from models.user import UserCreate, UserLogin, UserResponse, User
from services.auth_service import AuthService
from utils.auth import Token
from utils.auth_middleware import get_current_user

router = APIRouter()
auth_service = AuthService()


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """User registration endpoint"""
    try:
        user = await auth_service.register_user(user_data)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    """User login endpoint"""
    try:
        access_token = await auth_service.authenticate_user(login_data)
        return Token(access_token=access_token, token_type="bearer")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        preferred_llm_provider=current_user.preferred_llm_provider,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.post("/logout")
async def logout():
    """User logout endpoint - client-side token removal"""
    return {"message": "Logout successful. Please remove the token from client storage."}