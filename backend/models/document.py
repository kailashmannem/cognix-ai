"""Document and document chunk models"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId
import mimetypes

from models.user import PyObjectId


class Document(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    chat_id: str
    filename: str
    file_type: str
    file_size: int
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    processing_status: str = "pending"  # "pending", "processing", "completed", "failed"

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class DocumentChunk(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    document_id: str
    chat_id: str
    content: str
    chunk_index: int
    embedding: Optional[List[float]] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    upload_date: datetime
    processing_status: str

    model_config = {"from_attributes": True}


class DocumentChunkResponse(BaseModel):
    id: str
    content: str
    chunk_index: int

    model_config = {"from_attributes": True}


class DocumentValidation:
    """Additional validation methods for Document models"""
    
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
    }
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def validate_file_extension(filename: str) -> bool:
        """Validate file extension"""
        if not filename:
            return False
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        return extension in DocumentValidation.ALLOWED_EXTENSIONS
    
    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        """Validate file size"""
        return 0 < file_size <= DocumentValidation.MAX_FILE_SIZE
    
    @staticmethod
    def validate_mime_type(mime_type: str) -> bool:
        """Validate MIME type"""
        return mime_type in DocumentValidation.ALLOWED_MIME_TYPES
    
    @staticmethod
    def get_mime_type_from_filename(filename: str) -> Optional[str]:
        """Get MIME type from filename"""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type
    
    @staticmethod
    def validate_processing_status(status: str) -> bool:
        """Validate processing status"""
        allowed_statuses = {'pending', 'processing', 'completed', 'failed'}
        return status in allowed_statuses
    
    @staticmethod
    def validate_chunk_content(content: str) -> bool:
        """Validate document chunk content"""
        if not content or len(content.strip()) == 0:
            return False
        if len(content) > 5000:  # 5KB per chunk
            return False
        return True
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for storage"""
        # Remove path separators and other potentially harmful characters
        import re
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        sanitized = sanitized.strip()
        return sanitized[:255]  # Limit length


# Enhanced models with validation
class DocumentCreate(BaseModel):
    filename: str
    file_type: str
    file_size: int
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Filename cannot be empty')
        if not DocumentValidation.validate_file_extension(v):
            raise ValueError(f'File extension must be one of: {DocumentValidation.ALLOWED_EXTENSIONS}')
        return DocumentValidation.sanitize_filename(v)
    
    @field_validator('file_size')
    @classmethod
    def validate_size(cls, v):
        if not DocumentValidation.validate_file_size(v):
            raise ValueError(f'File size must be between 1 byte and {DocumentValidation.MAX_FILE_SIZE} bytes')
        return v
    
    @field_validator('file_type')
    @classmethod
    def validate_type(cls, v):
        if not DocumentValidation.validate_mime_type(v):
            raise ValueError(f'File type must be one of: {DocumentValidation.ALLOWED_MIME_TYPES}')
        return v


class DocumentChunkCreate(BaseModel):
    content: str
    chunk_index: int
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not DocumentValidation.validate_chunk_content(v):
            raise ValueError('Chunk content must be between 1 and 5000 characters')
        return v.strip()
    
    @field_validator('chunk_index')
    @classmethod
    def validate_index(cls, v):
        if v < 0:
            raise ValueError('Chunk index must be non-negative')
        return v


class DocumentStatusUpdate(BaseModel):
    processing_status: str
    
    @field_validator('processing_status')
    @classmethod
    def validate_status(cls, v):
        if not DocumentValidation.validate_processing_status(v):
            raise ValueError('Status must be one of: pending, processing, completed, failed')
        return v