from beanie import Document
from pydantic import Field
from typing import Optional
from datetime import datetime
from pymongo import IndexModel

from .enums import UserRole


class User(Document):
    """User model for MongoDB"""
    username: str = Field(..., max_length=50)
    email: str = Field(..., max_length=100)
    password_hash: str = Field(..., max_length=255)
    role: UserRole
    department: Optional[str] = Field(None, max_length=100)  # For state users
    state: Optional[str] = Field(None, max_length=100)  # For state users
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "users"
        indexes = [
            IndexModel("username", unique=True),
            IndexModel("email", unique=True),
        ]