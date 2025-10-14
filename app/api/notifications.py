from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from ..core.deps import get_current_user
from ..models.user import User
from ..models.notification import Notification, NotificationType, NotificationPriority
from ..services.notification_service import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    id: str
    type: str
    priority: str
    title: str
    message: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    is_read: bool
    created_at: str
    read_at: Optional[str]
    metadata: Optional[dict]

    class Config:
        from_attributes = True


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Get notifications for the current user"""
    
    notifications = await notification_service.get_notifications_for_user(str(current_user.id))
    
    # Apply filters
    if unread_only:
        notifications = [n for n in notifications if not n.is_read]
    
    # Apply limit
    notifications = notifications[:limit]
    
    return [
        NotificationResponse(
            id=str(n.id),
            type=n.type.value,
            priority=n.priority.value,
            title=n.title,
            message=n.message,
            resource_type=n.resource_type,
            resource_id=str(n.resource_id) if n.resource_id else None,
            is_read=n.is_read,
            created_at=n.created_at.isoformat(),
            read_at=n.read_at.isoformat() if n.read_at else None,
            metadata=n.notification_metadata
        )
        for n in notifications
    ]


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user)
):
    """Get count of unread notifications"""
    
    count = await notification_service.get_unread_count(str(current_user.id))
    
    return {"unread_count": count}


# Additional notification endpoints can be added later