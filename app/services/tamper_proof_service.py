import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from ..models.tamper_proof_log import TamperProofLog
from ..core.database import get_db


class TamperProofLoggingService:
    def __init__(self):
        self.genesis_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        self.db = get_db()

    def create_log_entry(
        self,
        action_type: str,
        resource_type: str,
        resource_id: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TamperProofLog:
        """Create a new tamper-proof log entry"""
        
        # Get the previous log entry (most recent by timestamp)
        previous_log = None
        if self.db.logs:
            previous_log = max(self.db.logs.values(), key=lambda x: x.timestamp)
        
        previous_hash = previous_log.chain_hash if previous_log else self.genesis_hash
        
        # Create log data
        log_data = {
            "action_type": action_type,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        # Generate data hash
        data_hash = self._generate_hash(json.dumps(log_data, sort_keys=True))
        
        # Generate chain hash (current data + previous hash)
        chain_data = f"{data_hash}{previous_hash}"
        chain_hash = self._generate_hash(chain_data)
        
        # Create log entry
        log_entry = TamperProofLog(
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            data_hash=data_hash,
            previous_hash=previous_hash,
            chain_hash=chain_hash,
            log_metadata=metadata
        )
        
        # Store in memory
        self.db.logs[log_entry.id] = log_entry
        
        return log_entry

    def verify_log_integrity(self) -> Dict[str, Any]:
        """Verify the integrity of the entire log chain"""
        
        logs = sorted(self.db.logs.values(), key=lambda x: x.timestamp)
        
        if not logs:
            return {"valid": True, "message": "No logs to verify"}
        
        verification_result = {
            "valid": True,
            "total_entries": len(logs),
            "verified_entries": 0,
            "errors": []
        }
        
        expected_previous_hash = self.genesis_hash
        
        for i, log in enumerate(logs):
            # Verify previous hash matches
            if log.previous_hash != expected_previous_hash:
                verification_result["valid"] = False
                verification_result["errors"].append({
                    "entry_id": str(log.id),
                    "position": i,
                    "error": "Previous hash mismatch",
                    "expected": expected_previous_hash,
                    "actual": log.previous_hash
                })
                continue
            
            # Verify data hash
            log_data = {
                "action_type": log.action_type,
                "resource_type": log.resource_type,
                "resource_id": str(log.resource_id),
                "user_id": str(log.user_id),
                "timestamp": log.timestamp.isoformat(),
                "metadata": log.log_metadata or {}
            }
            
            expected_data_hash = self._generate_hash(json.dumps(log_data, sort_keys=True))
            if log.data_hash != expected_data_hash:
                verification_result["valid"] = False
                verification_result["errors"].append({
                    "entry_id": str(log.id),
                    "position": i,
                    "error": "Data hash mismatch",
                    "expected": expected_data_hash,
                    "actual": log.data_hash
                })
                continue
            
            # Verify chain hash
            chain_data = f"{log.data_hash}{log.previous_hash}"
            expected_chain_hash = self._generate_hash(chain_data)
            if log.chain_hash != expected_chain_hash:
                verification_result["valid"] = False
                verification_result["errors"].append({
                    "entry_id": str(log.id),
                    "position": i,
                    "error": "Chain hash mismatch",
                    "expected": expected_chain_hash,
                    "actual": log.chain_hash
                })
                continue
            
            verification_result["verified_entries"] += 1
            expected_previous_hash = log.chain_hash
        
        return verification_result

    def get_audit_trail(
        self,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """Get audit trail with optional filtering"""
        
        logs = list(self.db.logs.values())
        
        # Apply filters
        if resource_type:
            logs = [log for log in logs if log.resource_type == resource_type]
        
        if resource_id:
            logs = [log for log in logs if log.resource_id == resource_id]
        
        if user_id:
            logs = [log for log in logs if log.user_id == user_id]
        
        # Sort by timestamp descending and limit
        logs = sorted(logs, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        return [self._format_log_entry(log) for log in logs]

    def _generate_hash(self, data: str) -> str:
        """Generate SHA-256 hash of data"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def get_audit_stats(self) -> Dict[str, Any]:
        """Get audit statistics"""
        logs = list(self.db.logs.values())
        
        if not logs:
            return {
                "total_log_entries": 0,
                "recent_activity_24h": 0,
                "action_type_distribution": [],
                "resource_type_distribution": []
            }
        
        # Count action types
        action_counts = {}
        resource_counts = {}
        recent_count = 0
        
        from datetime import timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        for log in logs:
            # Count action types
            action_counts[log.action_type] = action_counts.get(log.action_type, 0) + 1
            
            # Count resource types
            resource_counts[log.resource_type] = resource_counts.get(log.resource_type, 0) + 1
            
            # Count recent activity
            if log.timestamp >= yesterday:
                recent_count += 1
        
        return {
            "total_log_entries": len(logs),
            "recent_activity_24h": recent_count,
            "action_type_distribution": [
                {"action_type": action_type, "count": count}
                for action_type, count in action_counts.items()
            ],
            "resource_type_distribution": [
                {"resource_type": resource_type, "count": count}
                for resource_type, count in resource_counts.items()
            ]
        }

    def _format_log_entry(self, log: TamperProofLog) -> Dict[str, Any]:
        """Format log entry for API response"""
        return {
            "id": str(log.id),
            "action_type": log.action_type,
            "resource_type": log.resource_type,
            "resource_id": str(log.resource_id),
            "user_id": str(log.user_id),
            "timestamp": log.timestamp.isoformat(),
            "data_hash": log.data_hash,
            "previous_hash": log.previous_hash,
            "chain_hash": log.chain_hash,
            "metadata": log.log_metadata
        }

    # Convenience methods for common actions
    def log_document_upload(self, document_id: str, user_id: str, filename: str, file_hash: str):
        """Log document upload action"""
        return self.create_log_entry(
            action_type="document_upload",
            resource_type="document",
            resource_id=document_id,
            user_id=user_id,
            metadata={
                "filename": filename,
                "file_hash": file_hash,
                "action": "Document uploaded"
            }
        )

    def log_document_update(self, document_id: str, user_id: str, changes: Dict[str, Any]):
        """Log document update action"""
        return self.create_log_entry(
            action_type="document_update",
            resource_type="document",
            resource_id=document_id,
            user_id=user_id,
            metadata={
                "changes": changes,
                "action": "Document updated"
            }
        )

    def log_project_approval(self, project_id: str, user_id: str, approval_type: str, approved: bool):
        """Log project approval action"""
        return self.create_log_entry(
            action_type=f"{approval_type}_{'approve' if approved else 'reject'}",
            resource_type="project",
            resource_id=project_id,
            user_id=user_id,
            metadata={
                "approval_type": approval_type,
                "approved": approved,
                "action": f"{approval_type} {'approved' if approved else 'rejected'}"
            }
        )

    def log_comment_action(self, comment_id: str, user_id: str, action: str, content: Optional[str] = None):
        """Log comment action"""
        return self.create_log_entry(
            action_type=f"comment_{action}",
            resource_type="comment",
            resource_id=comment_id,
            user_id=user_id,
            metadata={
                "action": f"Comment {action}",
                "content_preview": content[:100] if content else None
            }
        )


# Global instance
tamper_proof_service = TamperProofLoggingService()