from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from ..models.enums import ProjectStatus, ProjectType


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    project_type: ProjectType
    department: str
    state: str


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[ProjectType] = None
    status: Optional[ProjectStatus] = None


class ProjectResponse(ProjectBase):
    id: str
    status: ProjectStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
    concept_note_approved: bool
    dpr_approved: bool
    sanctioned: bool
    funds_released: bool

    class Config:
        from_attributes = True


class ProjectListItem(BaseModel):
    id: str
    name: str
    project_type: ProjectType
    status: ProjectStatus
    department: str
    state: str
    created_at: datetime
    concept_note_approved: bool
    dpr_approved: bool
    sanctioned: bool
    funds_released: bool

    class Config:
        from_attributes = True


class ProjectFilter(BaseModel):
    status: Optional[ProjectStatus] = None
    project_type: Optional[ProjectType] = None
    department: Optional[str] = None
    state: Optional[str] = None
    search: Optional[str] = None