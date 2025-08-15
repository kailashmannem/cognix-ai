from fastapi import APIRouter

router = APIRouter()


@router.post("/upload")
async def upload_document():
    """Upload document for chat session"""
    return {"message": "Document upload endpoint - to be implemented"}


@router.get("/{document_id}")
async def get_document():
    """Get document information"""
    return {"message": "Get document endpoint - to be implemented"}


@router.delete("/{document_id}")
async def delete_document():
    """Delete document"""
    return {"message": "Delete document endpoint - to be implemented"}