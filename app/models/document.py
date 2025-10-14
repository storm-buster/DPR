from beanie import Document as BeanieDocument
from pydantic import Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from pymongo import IndexModel

from .enums import DocumentType, ValidationStatus


class Document(BeanieDocument):
    """Document model for MongoDB"""
    project_id: str  # Project ID
    filename: str = Field(..., max_length=255)
    document_type: DocumentType
    file_path: str = Field(..., max_length=500)  # MinIO/local storage path
    file_size: int
    mime_type: str = Field(..., max_length=100)
    hash_id: str = Field(..., max_length=64)  # SHA-256 hash
    version: int = 1
    is_current: bool = True
    uploaded_by: str  # User ID
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    
    # AI Validation
    ai_validation_status: ValidationStatus = ValidationStatus.PENDING
    ai_validation_results: Optional[Dict[str, Any]] = None
    
    # Related IDs (relationships handled via references)
    comment_ids: List[str] = Field(default_factory=list)
    validation_result_id: Optional[str] = None
    
    class Settings:
        name = "documents"
        indexes = [
            IndexModel("project_id"),
            IndexModel("document_type"),
            IndexModel("uploaded_by"),
            IndexModel("hash_id"),
        ]