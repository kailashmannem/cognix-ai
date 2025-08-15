"""Configuration settings using Pydantic Settings"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Platform Database (For user authentication)
    PLATFORM_MONGODB_URL: str = "mongodb://localhost:27017"
    PLATFORM_DATABASE_NAME: str = "cognix_platform"
    
    # Authentication
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    
    # LLM Providers
    DEFAULT_LLM_PROVIDER: str = "openai"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Vector Store
    VECTOR_STORE_TYPE: str = "faiss"
    VECTOR_STORE_PATH: str = "./vector_stores"
    
    # File Upload
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: str = "pdf,docx,txt"
    
    # HuggingFace
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"
    
    # Development
    DEBUG: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()