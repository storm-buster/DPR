from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from ..models.enums import DocumentType, ValidationStatus


class DocumentBase(BaseModel):
    filename: str
    document_type: DocumentType


class DocumentUpload(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    id: str
    project_id: str
    file_size: int
    mime_type: str
    hash_id: str
    version: int
    is_current: bool
    uploaded_by: str
    uploaded_at: datetime
    ai_validation_status: ValidationStatus
    ai_validation_results: Optional[dict] = None

    class Config:
        from_attributes = True


class DocumentUpdate(BaseModel):
    filename: Optional[str] = None
    document_type: Optional[DocumentType] = None


class DocumentVersion(BaseModel):
    id: str
    version: int
    filename: str
    uploaded_at: datetime
    is_current: bool
    hash_id: str

    class Config:
        from_attributes = True