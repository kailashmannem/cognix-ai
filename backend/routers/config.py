"""User configuration management API endpoints"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any

from models.user import User, UserConfig
from services.config_service import config_service
from utils.auth_middleware import get_current_user

router = APIRouter()


@router.get("/config", response_model=Dict[str, Any])
async def get_user_config(current_user: User = Depends(get_current_user)):
    """Get current user's configuration"""
    try:
        config = await config_service.get_user_config(str(current_user.id))
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve configuration: {str(e)}"
        )


@router.put("/config", response_model=Dict[str, Any])
async def update_user_config(
    config: UserConfig,
    current_user: User = Depends(get_current_user)
):
    """Update user configuration (API keys, database connection, preferences)"""
    try:
        result = await config_service.update_user_config(str(current_user.id), config)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )


@router.delete("/config/api-key/{provider}")
async def delete_api_key(
    provider: str,
    current_user: User = Depends(get_current_user)
):
    """Delete API key for a specific provider"""
    try:
        success = await config_service.delete_api_key(str(current_user.id), provider)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key for {provider} not found or could not be deleted"
            )
        return {"message": f"API key for {provider} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete API key: {str(e)}"
        )


@router.post("/config/test-database", response_model=Dict[str, Any])
async def test_database_connection(current_user: User = Depends(get_current_user)):
    """Test user's current database connection"""
    try:
        result = await config_service.test_user_database_connection(str(current_user.id))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test database connection: {str(e)}"
        )


@router.post("/config/validate-all", response_model=Dict[str, Any])
async def validate_all_configs(current_user: User = Depends(get_current_user)):
    """Validate all user configurations (API keys and database connection)"""
    try:
        result = await config_service.validate_all_user_configs(str(current_user.id))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate configurations: {str(e)}"
        )


@router.get("/config/api-key/{provider}")
async def get_api_key_status(
    provider: str,
    current_user: User = Depends(get_current_user)
):
    """Get status of API key for a specific provider (masked for security)"""
    try:
        config = await config_service.get_user_config(str(current_user.id))
        api_keys = config.get("api_keys", {})
        
        if provider not in api_keys:
            return {
                "provider": provider,
                "configured": False
            }
        
        return {
            "provider": provider,
            "configured": True,
            "masked_key": api_keys[provider].get("masked", "***"),
            "error": api_keys[provider].get("error")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get API key status: {str(e)}"
        )