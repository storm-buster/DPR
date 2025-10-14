import logging
from datetime import datetime
from typing import Optional, Dict, Any
from ..services.tamper_proof_service import tamper_proof_service


class AuditLogger:
    def __init__(self):
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # Create file handler for audit logs
        handler = logging.FileHandler("audit.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_security_event(
        self,
        event_type: str,
        user_id: Optional[str],
        ip_address: str,
        details: Dict[str, Any],
        severity: str = "INFO"
    ):
        """Log security-related events"""
        
        log_entry = {
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
            "severity": severity
        }
        
        self.logger.info(f"SECURITY_EVENT: {log_entry}")

    def log_authentication_attempt(
        self,
        username: str,
        ip_address: str,
        success: bool,
        failure_reason: Optional[str] = None
    ):
        """Log authentication attempts"""
        
        event_type = "LOGIN_SUCCESS" if success else "LOGIN_FAILURE"
        details = {
            "username": username,
            "success": success
        }
        
        if failure_reason:
            details["failure_reason"] = failure_reason
        
        severity = "INFO" if success else "WARNING"
        
        self.log_security_event(
            event_type=event_type,
            user_id=None,
            ip_address=ip_address,
            details=details,
            severity=severity
        )

    def log_authorization_failure(
        self,
        user_id: str,
        resource: str,
        action: str,
        ip_address: str
    ):
        """Log authorization failures"""
        
        self.log_security_event(
            event_type="AUTHORIZATION_FAILURE",
            user_id=user_id,
            ip_address=ip_address,
            details={
                "resource": resource,
                "action": action
            },
            severity="WARNING"
        )

    def log_file_upload(
        self,
        user_id: str,
        filename: str,
        file_size: int,
        file_hash: str,
        ip_address: str,
        validation_result: bool
    ):
        """Log file upload events"""
        
        self.log_security_event(
            event_type="FILE_UPLOAD",
            user_id=user_id,
            ip_address=ip_address,
            details={
                "filename": filename,
                "file_size": file_size,
                "file_hash": file_hash,
                "validation_passed": validation_result
            },
            severity="INFO"
        )

    def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        ip_address: str
    ):
        """Log data access events"""
        
        self.log_security_event(
            event_type="DATA_ACCESS",
            user_id=user_id,
            ip_address=ip_address,
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action": action
            },
            severity="INFO"
        )

    def log_suspicious_activity(
        self,
        user_id: Optional[str],
        activity_type: str,
        details: Dict[str, Any],
        ip_address: str
    ):
        """Log suspicious activities"""
        
        self.log_security_event(
            event_type="SUSPICIOUS_ACTIVITY",
            user_id=user_id,
            ip_address=ip_address,
            details={
                "activity_type": activity_type,
                **details
            },
            severity="ERROR"
        )

    def log_system_event(
        self,
        event_type: str,
        details: Dict[str, Any],
        severity: str = "INFO"
    ):
        """Log system-level events"""
        
        self.log_security_event(
            event_type=event_type,
            user_id=None,
            ip_address="system",
            details=details,
            severity=severity
        )

    def create_tamper_proof_log(
        self,
        action_type: str,
        resource_type: str,
        resource_id: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Create tamper-proof log entry"""
        
        return tamper_proof_service.create_log_entry(
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            metadata=metadata
        )


# Global instance
audit_logger = AuditLogger()