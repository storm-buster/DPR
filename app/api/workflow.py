from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from ..core.database import get_db
from ..core.deps import get_current_user, get_current_mdoner_user
from ..models.user import User
from ..models.project import Project
from ..models.document import Document
from ..models.enums import ProjectStatus, DocumentType

router = APIRouter(prefix="/workflow", tags=["workflow"])


class WorkflowAction(BaseModel):
    comment: Optional[str] = None
    approved: bool


@router.post("/approve-concept/{project_id}")
def approve_concept_note(
    project_id: str,
    action: WorkflowAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_mdoner_user)
):
    """Approve or reject concept note"""
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if concept note exists
    concept_note = db.query(Document).filter(
        Document.project_id == project_id,
        Document.document_type == DocumentType.CONCEPT_NOTE,
        Document.is_current == True
    ).first()
    
    if not concept_note:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No concept note found for this project"
        )
    
    if action.approved:
        project.concept_note_approved = True
        project.status = ProjectStatus.CONCEPT_APPROVED
        message = "Concept note approved successfully"
    else:
        project.concept_note_approved = False
        project.status = ProjectStatus.CONCEPT_REJECTED
        message = "Concept note rejected"
    
    db.commit()
    
    return {
        "message": message,
        "project_id": project_id,
        "status": project.status,
        "comment": action.comment
    }


@router.post("/approve-dpr/{project_id}")
def approve_dpr(
    project_id: str,
    action: WorkflowAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_mdoner_user)
):
    """Approve or reject DPR"""
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if concept note is approved
    if not project.concept_note_approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Concept note must be approved before DPR approval"
        )
    
    # Check if DPR exists
    dpr = db.query(Document).filter(
        Document.project_id == project_id,
        Document.document_type == DocumentType.DPR,
        Document.is_current == True
    ).first()
    
    if not dpr:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No DPR found for this project"
        )
    
    if action.approved:
        project.dpr_approved = True
        project.status = ProjectStatus.DPR_APPROVED
        message = "DPR approved successfully"
    else:
        project.dpr_approved = False
        project.status = ProjectStatus.DPR_REJECTED
        message = "DPR rejected"
    
    db.commit()
    
    return {
        "message": message,
        "project_id": project_id,
        "status": project.status,
        "comment": action.comment
    }


@router.post("/sanction-project/{project_id}")
def sanction_project(
    project_id: str,
    action: WorkflowAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_mdoner_user)
):
    """Sanction project after DPR approval"""
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check prerequisites
    if not project.concept_note_approved or not project.dpr_approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both concept note and DPR must be approved before sanctioning"
        )
    
    if action.approved:
        project.sanctioned = True
        project.status = ProjectStatus.SANCTIONED
        message = "Project sanctioned successfully"
    else:
        message = "Project sanctioning declined"
    
    db.commit()
    
    return {
        "message": message,
        "project_id": project_id,
        "status": project.status,
        "comment": action.comment
    }


@router.post("/release-funds/{project_id}")
def release_funds(
    project_id: str,
    action: WorkflowAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_mdoner_user)
):
    """Release funds for sanctioned project"""
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if project is sanctioned
    if not project.sanctioned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project must be sanctioned before fund release"
        )
    
    # Check if funds already released
    if project.funds_released:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Funds have already been released for this project"
        )
    
    if action.approved:
        project.funds_released = True
        project.status = ProjectStatus.FUND_RELEASED
        message = "Funds released successfully"
    else:
        project.status = ProjectStatus.FUND_REQUESTED  # Keep in requested state
        message = "Fund release declined"
    
    db.commit()
    
    return {
        "message": message,
        "project_id": project_id,
        "status": project.status,
        "comment": action.comment
    }


@router.post("/start-implementation/{project_id}")
def start_implementation(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark project as under implementation"""
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions
    if (current_user.role == "state_user" and 
        project.created_by != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this project"
        )
    
    # Check if funds are released
    if not project.funds_released:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Funds must be released before starting implementation"
        )
    
    project.status = ProjectStatus.UNDER_IMPLEMENTATION
    db.commit()
    
    return {
        "message": "Project implementation started",
        "project_id": project_id,
        "status": project.status
    }


@router.post("/complete-project/{project_id}")
def complete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark project as completed"""
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions
    if (current_user.role == "state_user" and 
        project.created_by != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this project"
        )
    
    # Check if project is under implementation
    if project.status != ProjectStatus.UNDER_IMPLEMENTATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project must be under implementation to mark as completed"
        )
    
    project.status = ProjectStatus.COMPLETED
    db.commit()
    
    return {
        "message": "Project marked as completed",
        "project_id": project_id,
        "status": project.status
    }


@router.get("/status/{project_id}")
def get_workflow_status(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed workflow status for a project"""
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions
    if (current_user.role == "state_user" and 
        project.created_by != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this project"
        )
    
    # Get document status
    concept_note = db.query(Document).filter(
        Document.project_id == project_id,
        Document.document_type == DocumentType.CONCEPT_NOTE,
        Document.is_current == True
    ).first()
    
    dpr = db.query(Document).filter(
        Document.project_id == project_id,
        Document.document_type == DocumentType.DPR,
        Document.is_current == True
    ).first()
    
    workflow_status = {
        "project_id": project_id,
        "current_status": project.status,
        "workflow_stages": {
            "concept_note": {
                "submitted": concept_note is not None,
                "approved": project.concept_note_approved,
                "document_id": str(concept_note.id) if concept_note else None
            },
            "dpr": {
                "submitted": dpr is not None,
                "approved": project.dpr_approved,
                "document_id": str(dpr.id) if dpr else None
            },
            "sanctioned": project.sanctioned,
            "funds_released": project.funds_released
        },
        "next_actions": _get_next_actions(project, concept_note, dpr, current_user.role),
        "can_proceed": _can_proceed_to_next_stage(project, concept_note, dpr)
    }
    
    return workflow_status


def _get_next_actions(project: Project, concept_note: Document, dpr: Document, user_role: str) -> list:
    """Determine next possible actions based on current state"""
    actions = []
    
    if user_role == "state_user":
        if not concept_note:
            actions.append("Upload concept note")
        elif concept_note and not project.concept_note_approved and project.status == ProjectStatus.DRAFT:
            actions.append("Submit concept note for review")
        elif project.concept_note_approved and not dpr:
            actions.append("Upload DPR")
        elif dpr and not project.dpr_approved and project.concept_note_approved:
            actions.append("Submit DPR for review")
        elif project.sanctioned and not project.funds_released:
            actions.append("Request fund release")
        elif project.funds_released and project.status != ProjectStatus.UNDER_IMPLEMENTATION:
            actions.append("Start implementation")
        elif project.status == ProjectStatus.UNDER_IMPLEMENTATION:
            actions.append("Mark project as completed")
    
    elif user_role == "mdoner_user":
        if concept_note and project.status == ProjectStatus.CONCEPT_SUBMITTED:
            actions.append("Review concept note")
        elif dpr and project.status == ProjectStatus.DPR_SUBMITTED:
            actions.append("Review DPR")
        elif project.dpr_approved and not project.sanctioned:
            actions.append("Sanction project")
        elif project.status == ProjectStatus.FUND_REQUESTED:
            actions.append("Review fund release request")
    
    return actions


def _can_proceed_to_next_stage(project: Project, concept_note: Document, dpr: Document) -> bool:
    """Check if project can proceed to next workflow stage"""
    
    if not concept_note:
        return False
    
    if not project.concept_note_approved:
        return False
    
    if project.concept_note_approved and not dpr:
        return False
    
    if dpr and not project.dpr_approved:
        return False
    
    return True