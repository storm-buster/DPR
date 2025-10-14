from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from io import BytesIO
import hashlib
import uuid
from datetime import datetime

from ..core.deps import get_current_user
from ..models.user import User
from ..models.document import Document
from ..models.enums import DocumentType, ValidationStatus
from ..services.document_service import document_service
from ..services.project_service import project_service
from ..services.local_file_service import local_file_service

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain',
    'image/jpeg',
    'image/png'
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/upload/{project_id}")
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    document_type: DocumentType = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Upload a document to a project"""
    
    # Validate project exists and user has access
    project = project_service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if state user owns the project or if MDONER user
    if (current_user.role == "state_user" and 
        project.created_by != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to upload to this project"
        )
    
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed"
        )
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum allowed size"
        )
    
    # Get existing documents of same type
    existing_docs = [doc for doc in document_service.get_documents_by_project(project_id)
                    if doc.document_type == document_type and doc.is_current]
    
    # Calculate next version number
    max_version = 0
    if existing_docs:
        max_version = max(doc.version for doc in existing_docs)
        # Mark existing documents as not current
        for doc in existing_docs:
            document_service.update_document(doc.id, is_current=False)
    
    try:
        # Generate file hash
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Generate file path for local storage
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = file.filename.replace(" ", "_").replace("/", "_")
        file_path = f"projects/{project_id}/{document_type.value}/{timestamp}_{unique_id}_{safe_filename}"
        
        # Store file locally
        stored_path, _ = await local_file_service.upload_file(
            file_content, file_path, file.content_type
        )
        
        # Create document record
        document = document_service.create_document(
            project_id=project_id,
            filename=file.filename,
            document_type=document_type,
            file_path=stored_path,
            file_size=file_size,
            mime_type=file.content_type,
            hash_id=file_hash,
            uploaded_by=current_user.id
        )
        
        # Update version and current status
        document_service.update_document(
            document.id,
            version=max_version + 1,
            is_current=True,
            ai_validation_status=ValidationStatus.PENDING
        )
        
        return {
            "id": document.id,
            "filename": document.filename,
            "document_type": document.document_type,
            "file_size": document.file_size,
            "hash_id": document.hash_id,
            "version": max_version + 1,
            "uploaded_at": document.uploaded_at.isoformat(),
            "ai_validation_status": "pending",
            "message": "Document uploaded successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get("/project/{project_id}")
def get_project_documents(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all documents for a project"""
    
    # Validate project exists and user has access
    project = project_service.get_project_by_id(project_id)
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
            detail="Not authorized to view this project's documents"
        )
    
    documents = document_service.get_documents_by_project(project_id)
    
    # Convert to response format
    document_list = []
    for doc in documents:
        document_list.append({
            "id": doc.id,
            "filename": doc.filename,
            "document_type": doc.document_type,
            "file_size": doc.file_size,
            "mime_type": doc.mime_type,
            "hash_id": doc.hash_id,
            "version": doc.version,
            "is_current": doc.is_current,
            "uploaded_by": doc.uploaded_by,
            "uploaded_at": doc.uploaded_at.isoformat(),
            "ai_validation_status": doc.ai_validation_status,
            "ai_validation_results": doc.ai_validation_results
        })
    
    # Sort by uploaded_at descending
    document_list.sort(key=lambda x: x["uploaded_at"], reverse=True)
    
    return document_list


@router.get("/{document_id}")
def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get document details"""
    
    document = document_service.get_document_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check access permissions
    project = project_service.get_project_by_id(document.project_id)
    if (current_user.role == "state_user" and 
        project.created_by != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this document"
        )
    
    return {
        "id": document.id,
        "filename": document.filename,
        "document_type": document.document_type,
        "file_size": document.file_size,
        "mime_type": document.mime_type,
        "hash_id": document.hash_id,
        "version": document.version,
        "is_current": document.is_current,
        "uploaded_by": document.uploaded_by,
        "uploaded_at": document.uploaded_at.isoformat(),
        "ai_validation_status": document.ai_validation_status,
        "ai_validation_results": document.ai_validation_results
    }


# Additional endpoints can be added later for download and versions


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a document"""
    
    document = document_service.get_document_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check access permissions - only document uploader or MDONER can delete
    if (current_user.role == "state_user" and 
        document.uploaded_by != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this document"
        )
    
    try:
        # Delete from local storage
        await local_file_service.delete_file(document.file_path)
        
        # Delete from in-memory database
        document_service.delete_document(document_id)
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )