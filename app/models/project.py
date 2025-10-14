from beanie import Document
from pydantic import Field
from typing import Optional, List
from datetime import datetime
from pymongo import IndexModel

from .enums import ProjectStatus, ProjectType


class Project(Document):
    """Project model for MongoDB"""
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    project_type: ProjectType
    status: ProjectStatus = ProjectStatus.DRAFT
    department: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    created_by: str  # User ID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Workflow status flags
    concept_note_approved: bool = False
    dpr_approved: bool = False
    sanctioned: bool = False
    funds_released: bool = False
    
    # Document IDs (relationships handled via references)
    document_ids: List[str] = Field(default_factory=list)
    
    class Settings:
        name = "projects"
        indexes = [
            IndexModel("created_by"),
            IndexModel("status"),
            IndexModel("department"),
            IndexModel("state"),
        ]