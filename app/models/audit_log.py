from beanie import Document
from pydantic import Field
from typing import Optional, Dict, Any
from datetime import datetime
from pymongo import IndexModel


class AuditLog(Document):
    """Audit log model for MongoDB"""
    user_id: str  # User who performed the action
    action: str = Field(..., max_length=100)  # Action performed
    resource_type: str = Field(..., max_length=50)  # Type of resource (project, document, etc.)
    resource_id: str  # ID of the resource
    details: Optional[Dict[str, Any]] = None  # Additional details about the action
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "audit_logs"
        indexes = [
            IndexModel("user_id"),
            IndexModel("resource_type"),
            IndexModel("resource_id"),
            IndexModel("timestamp"),
        ]