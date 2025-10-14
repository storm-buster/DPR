from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from .enums import ActionType


class TamperProofLog(BaseModel):
    """Tamper Proof Log model for in-memory storage (will be converted to MongoDB later)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_type: str = Field(..., max_length=50)  # Using String for flexibility
    resource_type: str = Field(..., max_length=50)  # document, project, user, etc.
    resource_id: str  # Resource ID
    user_id: str  # User ID
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data_hash: str = Field(..., max_length=64)  # SHA-256 hash of the action data
    previous_hash: Optional[str] = Field(None, max_length=64)  # Hash of previous log entry
    chain_hash: str = Field(..., max_length=64)  # Hash of current + previous
    log_metadata: Optional[Dict[str, Any]] = None  # Additional action metadata