from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query

from ..core.database import get_db
from ..core.deps import get_current_user, get_current_mdoner_user
from ..models.user import User
from ..services.tamper_proof_service import tamper_proof_service

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/trail")
def get_audit_trail(
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """Get audit trail with optional filtering"""
    
    # State users can only see their own actions or actions on their resources
    if current_user.role == "state_user":
        # For state users, filter to their own actions or their projects
        if user_id and user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="State users can only view their own audit trail"
            )
        user_id = str(current_user.id)
    
    # MDONER users can see all audit trails (no additional filtering)
    
    audit_trail = tamper_proof_service.get_audit_trail(
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        limit=limit
    )
    
    return {
        "audit_trail": audit_trail,
        "total_entries": len(audit_trail),
        "filters": {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_id": user_id,
            "limit": limit
        }
    }


@router.get("/verify-integrity")
def verify_log_integrity(
    current_user: User = Depends(get_current_mdoner_user)
):
    """Verify the integrity of the tamper-proof log chain (MDONER only)"""
    
    verification_result = tamper_proof_service.verify_log_integrity()
    
    return {
        "verification_result": verification_result,
        "verified_by": current_user.username,
        "verification_timestamp": tamper_proof_service._format_log_entry(
            type('obj', (object,), {'timestamp': tamper_proof_service.datetime.utcnow()})()
        )["timestamp"] if hasattr(tamper_proof_service, 'datetime') else None
    }


@router.get("/resource/{resource_type}/{resource_id}")
def get_resource_audit_trail(
    resource_type: str,
    resource_id: str,
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user)
):
    """Get audit trail for a specific resource"""
    
    # Check if user has access to this resource
    if current_user.role == "state_user":
        # Additional access checks would go here based on resource type
        # For now, we'll allow access to their own resources
        pass
    
    audit_trail = tamper_proof_service.get_audit_trail(
        resource_type=resource_type,
        resource_id=resource_id,
        limit=limit
    )
    
    return {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "audit_trail": audit_trail,
        "total_entries": len(audit_trail)
    }


@router.get("/user/{user_id}")
def get_user_audit_trail(
    user_id: str,
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user)
):
    """Get audit trail for a specific user"""
    
    # Users can only see their own audit trail, MDONER can see any
    if current_user.role == "state_user" and user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own audit trail"
        )
    
    audit_trail = tamper_proof_service.get_audit_trail(
        user_id=user_id,
        limit=limit
    )
    
    return {
        "user_id": user_id,
        "audit_trail": audit_trail,
        "total_entries": len(audit_trail)
    }


@router.get("/stats")
def get_audit_stats(
    current_user: User = Depends(get_current_mdoner_user)
):
    """Get audit statistics (MDONER only)"""
    
    return tamper_proof_service.get_audit_stats()