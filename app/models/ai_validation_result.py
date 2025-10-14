from beanie import Document
from pydantic import Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from pymongo import IndexModel


class AIValidationResult(Document):
    """AI Validation Result model for MongoDB"""
    document_id: str  # Document ID
    completeness_score: float
    missing_fields: Optional[List[str]] = None
    inconsistencies: Optional[List[str]] = None
    summary_report: Optional[str] = Field(None, max_length=2000)
    validation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    ai_model_version: str = Field(..., max_length=50)
    detailed_analysis: Optional[Dict[str, Any]] = None  # Store detailed AI analysis results
    
    class Settings:
        name = "ai_validation_results"
        indexes = [
            IndexModel("document_id"),
            IndexModel("validation_timestamp"),
        ]