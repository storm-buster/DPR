from beanie import Document
from pydantic import Field
from datetime import datetime
from pymongo import IndexModel


class Comment(Document):
    """Comment model for MongoDB"""
    document_id: str  # Document ID
    project_id: str  # Project ID for easier querying
    user_id: str  # User ID
    user_name: str  # User name for display
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_deleted: bool = False
    
    class Settings:
        name = "comments"
        indexes = [
            IndexModel("document_id"),
            IndexModel("project_id"),
            IndexModel("user_id"),
        ]