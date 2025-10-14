from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.user import User
from ..models.document import Document
from ..models.project import Project
from ..schemas.document import DocumentVersion

router = APIRouter(prefix="/document-versions", tags=["document-versions"])


@router.get("/{document_id}/history", response_model=List[DocumentVersion])
def get_document_history(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get complete version history for a document"""
    
    # Get the document to verify access
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check access permissions
    project = db.query(Project).filter(Project.id == document.project_id).first()
    if (current_user.role == "state_user" and 
        project.created_by != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this document's history"
        )
    
    # Get all versions of documents with same type in same project
    versions = db.query(Document).filter(
        Document.project_id == document.project_id,
        Document.document_type == document.document_type
    ).order_by(Document.version.desc()).all()
    
    return versions


@router.get("/project/{project_id}/type/{document_type}", response_model=List[DocumentVersion])
def get_document_versions_by_type(
    project_id: str,
    document_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all versions of a specific document type in a project"""
    
    # Verify project access
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if (current_user.role == "state_user" and 
        project.created_by != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this project's documents"
        )
    
    # Get all versions of the specified document type
    versions = db.query(Document).filter(
        Document.project_id == project_id,
        Document.document_type == document_type
    ).order_by(Document.version.desc()).all()
    
    return versions


@router.post("/{document_id}/revert/{version}")
def revert_to_version(
    document_id: str,
    version: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revert to a specific version of a document"""
    
    # Get the current document
    current_document = db.query(Document).filter(Document.id == document_id).first()
    if not current_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check access permissions
    project = db.query(Project).filter(Project.id == current_document.project_id).first()
    if (current_user.role == "state_user" and 
        project.created_by != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to revert this document"
        )
    
    # Find the version to revert to
    target_version = db.query(Document).filter(
        Document.project_id == current_document.project_id,
        Document.document_type == current_document.document_type,
        Document.version == version
    ).first()
    
    if not target_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version} not found"
        )
    
    # Mark current document as not current
    current_document.is_current = False
    
    # Mark target version as current
    target_version.is_current = True
    
    db.commit()
    
    return {
        "message": f"Successfully reverted to version {version}",
        "current_version": version,
        "document_id": target_version.id
    }


@router.get("/{document_id}/compare/{other_document_id}")
def compare_document_versions(
    document_id: str,
    other_document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compare two versions of a document"""
    
    # Get both documents
    doc1 = db.query(Document).filter(Document.id == document_id).first()
    doc2 = db.query(Document).filter(Document.id == other_document_id).first()
    
    if not doc1 or not doc2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both documents not found"
        )
    
    # Verify they are from the same project and document type
    if (doc1.project_id != doc2.project_id or 
        doc1.document_type != doc2.document_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Documents must be from the same project and of the same type"
        )
    
    # Check access permissions
    project = db.query(Project).filter(Project.id == doc1.project_id).first()
    if (current_user.role == "state_user" and 
        project.created_by != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to compare these documents"
        )
    
    # Return comparison metadata
    return {
        "document1": {
            "id": doc1.id,
            "version": doc1.version,
            "filename": doc1.filename,
            "uploaded_at": doc1.uploaded_at,
            "file_size": doc1.file_size,
            "hash_id": doc1.hash_id,
            "is_current": doc1.is_current
        },
        "document2": {
            "id": doc2.id,
            "version": doc2.version,
            "filename": doc2.filename,
            "uploaded_at": doc2.uploaded_at,
            "file_size": doc2.file_size,
            "hash_id": doc2.hash_id,
            "is_current": doc2.is_current
        },
        "comparison": {
            "version_difference": abs(doc1.version - doc2.version),
            "size_difference": doc2.file_size - doc1.file_size,
            "time_difference": (doc2.uploaded_at - doc1.uploaded_at).total_seconds(),
            "hash_changed": doc1.hash_id != doc2.hash_id
        }
    }