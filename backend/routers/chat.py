from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_chats():
    """Get user's chat sessions"""
    return {"message": "Get chats endpoint - to be implemented"}


@router.post("/")
async def create_chat():
    """Create new chat session"""
    return {"message": "Create chat endpoint - to be implemented"}


@router.get("/{chat_id}")
async def get_chat():
    """Get specific chat session"""
    return {"message": "Get chat endpoint - to be implemented"}


@router.post("/{chat_id}/messages")
async def send_message():
    """Send message to chat"""
    return {"message": "Send message endpoint - to be implemented"}


@router.delete("/{chat_id}")
async def delete_chat():
    """Delete chat session"""
    return {"message": "Delete chat endpoint - to be implemented"}