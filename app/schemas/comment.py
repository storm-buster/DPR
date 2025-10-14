from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    pass


class CommentUpdate(BaseModel):
    content: str


class CommentResponse(CommentBase):
    id: str
    document_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    
    # User information
    user_name: str
    user_role: str

    class Config:
        from_attributes = True