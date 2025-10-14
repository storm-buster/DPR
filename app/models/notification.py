from beanie import Document
from pydantic import Field
from typing import Optional, Dict, Any
from datetime import datetime
from pymongo import IndexModel
from enum import Enum as PyEnum


class NotificationType(str, PyEnum):
    PROJECT_APPROVED = "project_approved"
    PROJECT_REJECTED = "project_rejected"
    DOCUMENT_UPLOADED = "document_uploaded"
    COMMENT_ADDED = "comment_added"
    WORKFLOW_UPDATE = "workflow_update"
    FUND_RELEASED = "fund_released"
    SYSTEM_ALERT = "system_alert"


class NotificationPriority(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Notification(Document):
    """Notification model for MongoDB"""
    user_id: str  # User ID
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM
    title: str = Field(..., max_length=200)
    message: str = Field(..., max_length=1000)
    
    # Related resource information
    resource_type: Optional[str] = Field(None, max_length=50)  # project, document, comment
    resource_id: Optional[str] = None
    
    # Notification state
    is_read: bool = False
    is_sent: bool = False
    
    # Metadata for additional context
    notification_metadata: Optional[Dict[str, Any]] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    
    class Settings:
        name = "notifications"
        indexes = [
            IndexModel("user_id"),
            IndexModel("is_read"),
            IndexModel("type"),
        ]