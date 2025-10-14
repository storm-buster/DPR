from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.user import User
from ..models.document import Document
from ..models.comment import Comment
from ..models.project import Project
from ..schemas.comment import CommentCreate, CommentResponse, CommentUpdate

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get("/document/{document_id}", response_model=List[CommentResponse])
def get_document_comments(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all comments for a document"""
    
    # Verify document exists and user has access
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
            detail="Not authorized to view comments on this document"
        )
    
    # Get comments with user information
    comments = db.query(Comment).options(
        joinedload(Comment.user)
    ).filter(
        Comment.document_id == document_id,
        Comment.is_deleted == False
    ).order_by(Comment.created_at.asc()).all()
    
    # Format response with user information
    comment_responses = []
    for comment in comments:
        comment_data = {
            "id": str(comment.id),
            "document_id": str(comment.document_id),
            "user_id": str(comment.user_id),
            "content": comment.content,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
            "is_deleted": comment.is_deleted,
            "user_name": comment.user.username,
            "user_role": comment.user.role.value
        }
        comment_responses.append(CommentResponse(**comment_data))
    
    return comment_responses


@router.post("/document/{document_id}", response_model=CommentResponse)
def add_comment(
    document_id: str,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a comment to a document"""
    
    # Verify document exists and user has access
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
            detail="Not authorized to comment on this document"
        )
    
    # Create comment
    comment = Comment(
        document_id=document_id,
        user_id=current_user.id,
        content=comment_data.content
    )
    
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    # Return comment with user information
    comment_response = CommentResponse(
        id=str(comment.id),
        document_id=str(comment.document_id),
        user_id=str(comment.user_id),
        content=comment.content,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        is_deleted=comment.is_deleted,
        user_name=current_user.username,
        user_role=current_user.role.value
    )
    
    return comment_response


@router.put("/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: str,
    comment_update: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a comment (only by the comment author)"""
    
    comment = db.query(Comment).options(
        joinedload(Comment.user)
    ).filter(Comment.id == comment_id).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Only the comment author can update their comment
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only update your own comments"
        )
    
    # Update comment
    comment.content = comment_update.content
    db.commit()
    db.refresh(comment)
    
    # Return updated comment with user information
    comment_response = CommentResponse(
        id=str(comment.id),
        document_id=str(comment.document_id),
        user_id=str(comment.user_id),
        content=comment.content,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        is_deleted=comment.is_deleted,
        user_name=comment.user.username,
        user_role=comment.user.role.value
    )
    
    return comment_response


@router.delete("/{comment_id}")
def delete_comment(
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a comment (soft delete)"""
    
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Only the comment author or MDONER users can delete comments
    if (comment.user_id != current_user.id and 
        current_user.role != "mdoner_user"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only delete your own comments"
        )
    
    # Soft delete
    comment.is_deleted = True
    db.commit()
    
    return {"message": "Comment deleted successfully"}


@router.get("/project/{project_id}", response_model=List[CommentResponse])
def get_project_comments(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all comments for all documents in a project"""
    
    # Verify project exists and user has access
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check access permissions
    if (current_user.role == "state_user" and 
        project.created_by != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view comments on this project"
        )
    
    # Get all comments for documents in this project
    comments = db.query(Comment).options(
        joinedload(Comment.user),
        joinedload(Comment.document)
    ).join(Document).filter(
        Document.project_id == project_id,
        Comment.is_deleted == False
    ).order_by(Comment.created_at.desc()).all()
    
    # Format response with user information
    comment_responses = []
    for comment in comments:
        comment_data = {
            "id": str(comment.id),
            "document_id": str(comment.document_id),
            "user_id": str(comment.user_id),
            "content": comment.content,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
            "is_deleted": comment.is_deleted,
            "user_name": comment.user.username,
            "user_role": comment.user.role.value
        }
        comment_responses.append(CommentResponse(**comment_data))
    
    return comment_responses


@router.get("/recent", response_model=List[CommentResponse])
def get_recent_comments(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent comments for projects accessible to the user"""
    
    # Build query based on user role
    query = db.query(Comment).options(
        joinedload(Comment.user),
        joinedload(Comment.document).joinedload(Document.project)
    ).join(Document).join(Project)
    
    if current_user.role == "state_user":
        # State users can only see comments on their own projects
        query = query.filter(Project.created_by == current_user.id)
    # MDONER users can see all comments (no additional filter needed)
    
    comments = query.filter(
        Comment.is_deleted == False
    ).order_by(Comment.created_at.desc()).limit(limit).all()
    
    # Format response with user information
    comment_responses = []
    for comment in comments:
        comment_data = {
            "id": str(comment.id),
            "document_id": str(comment.document_id),
            "user_id": str(comment.user_id),
            "content": comment.content,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
            "is_deleted": comment.is_deleted,
            "user_name": comment.user.username,
            "user_role": comment.user.role.value
        }
        comment_responses.append(CommentResponse(**comment_data))
    
    return comment_responses