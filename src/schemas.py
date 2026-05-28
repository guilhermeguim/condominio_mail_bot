from pydantic import BaseModel
from typing import Optional

class DocumentSchema(BaseModel):
    file_id: str
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    
class MessageSchema(BaseModel):
    document: Optional[DocumentSchema] = None

class TelegramUpdateSchema(BaseModel):
    message: Optional[MessageSchema] = None