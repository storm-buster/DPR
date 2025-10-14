from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from ..core.deps import get_current_user, get_current_state_user, get_current_mdoner_user
from ..models.user import User
from ..models.project import Project
from ..models.enums import ProjectStatus, ProjectType
from ..services.project_service import project_service
from ..schemas.project import (
    ProjectCreate, 
    ProjectResponse, 
    ProjectUpdate, 
    ProjectListItem,
    ProjectFilter
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_state_user)
):
    """Create a new project (State users only)"""
    
    # Validate that state user is creating project for their department/state
    if (project_data.department != current_user.department or 
        project_data.state != current_user.state):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only create projects for your own department and state"
        )
    
    project = await project_service.create_project(
        name=project_data.name,
        description=project_data.description,
        project_type=project_data.project_type,
        department=project_data.department,
        state=project_data.state,
        created_by=str(current_user.id)
    )
    
    return project


@router.get("/", response_model=List[ProjectListItem])
async def list_projects(
    status: Optional[ProjectStatus] = Query(None),
    project_type: Optional[ProjectType] = Query(None),
    department: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """List projects with filtering and pagination"""
    
    # Apply role-based filtering
    user_filter = None
    if current_user.role == "state_user":
        # State users can only see their own projects
        user_filter = str(current_user.id)
    # MDONER users can see all projects (no user filter)
    
    # Get filtered projects
    projects = await project_service.filter_projects(
        user_id=user_filter,
        status=status,
        project_type=project_type,
        department=department,
        state=state,
        search=search
    )
    
    # Apply pagination
    total = len(projects)
    projects = projects[skip:skip + limit]
    
    return projects


@router.get("/pending-verification", response_model=List[ProjectListItem])
async def get_pending_verification_projects(
    current_user: User = Depends(get_current_mdoner_user)
):
    """Get projects pending verification (MDONER users only)"""
    
    # Projects that need MDONER attention
    pending_statuses = [
        ProjectStatus.CONCEPT_SUBMITTED,
        ProjectStatus.DPR_SUBMITTED,
        ProjectStatus.FUND_REQUESTED
    ]
    
    projects = await project_service.get_projects_by_statuses(pending_statuses)
    
    # Sort by updated_at ascending (oldest first)
    projects.sort(key=lambda x: x.updated_at)
    
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get project details"""
    
    project = await project_service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check access permissions
    if (current_user.role == "state_user" and 
        project.created_by != str(current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this project"
        )
    
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update project details"""
    
    project = project_service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions
    if current_user.role == "state_user":
        # State users can only update their own projects
        if project.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this project"
            )
        # State users cannot directly change status (workflow controlled)
        if project_update.status is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot directly update project status"
            )
    
    # Update fields
    update_data = project_update.dict(exclude_unset=True)
    updated_project = project_service.update_project(project_id, **update_data)
    
    return updated_project


@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a project"""
    
    project = project_service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions
    if current_user.role == "state_user":
        # State users can only delete their own projects in draft status
        if project.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this project"
            )
        if project.status != ProjectStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only delete projects in draft status"
            )
    
    project_service.delete_project(project_id)
    
    return {"message": "Project deleted successfully"}


@router.post("/{project_id}/submit-concept")
def submit_concept_note(
    project_id: str,
    current_user: User = Depends(get_current_state_user)
):
    """Submit concept note for review"""
    
    project = project_service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions
    if project.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to submit this project"
        )
    
    # For now, skip document validation since documents aren't implemented yet
    # TODO: Add document validation when document service is implemented
    
    # Update project status
    project_service.update_project(project_id, status=ProjectStatus.CONCEPT_SUBMITTED)
    
    return {"message": "Concept note submitted for review"}


@router.post("/{project_id}/submit-dpr")
def submit_dpr(
    project_id: str,
    current_user: User = Depends(get_current_state_user)
):
    """Submit DPR for review"""
    
    project = project_service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions
    if project.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to submit this project"
        )
    
    # Check if concept note is approved
    if not project.concept_note_approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Concept note must be approved before submitting DPR"
        )
    
    # For now, skip document validation since documents aren't implemented yet
    # TODO: Add document validation when document service is implemented
    
    # Update project status
    project_service.update_project(project_id, status=ProjectStatus.DPR_SUBMITTED)
    
    return {"message": "DPR submitted for review"}


@router.post("/{project_id}/request-funds")
def request_fund_release(
    project_id: str,
    current_user: User = Depends(get_current_state_user)
):
    """Request fund release for sanctioned project"""
    
    project = project_service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions
    if project.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to request funds for this project"
        )
    
    # Check if project is sanctioned
    if not project.sanctioned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project must be sanctioned before requesting funds"
        )
    
    # Update project status
    project_service.update_project(project_id, status=ProjectStatus.FUND_REQUESTED)
    
    return {"message": "Fund release requested"}


@router.get("/{project_id}/documents")
async def get_project_documents(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all documents for a project - redirect to documents API"""
    
    # Validate project exists and user has access
    project = await project_service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check access permissions
    if (current_user.role == "state_user" and 
        project.created_by != str(current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this project's documents"
        )
    
    # For now, return empty list since we're transitioning to MongoDB
    # This will be properly implemented once document service is updated
    return []