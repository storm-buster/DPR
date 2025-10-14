from enum import Enum


class UserRole(str, Enum):
    STATE_USER = "state_user"
    MDONER_USER = "mdoner_user"


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    CONCEPT_SUBMITTED = "concept_submitted"
    CONCEPT_APPROVED = "concept_approved"
    CONCEPT_REJECTED = "concept_rejected"
    DPR_SUBMITTED = "dpr_submitted"
    DPR_APPROVED = "dpr_approved"
    DPR_REJECTED = "dpr_rejected"
    SANCTIONED = "sanctioned"
    FUND_REQUESTED = "fund_requested"
    FUND_RELEASED = "fund_released"
    UNDER_IMPLEMENTATION = "under_implementation"
    COMPLETED = "completed"


class ProjectType(str, Enum):
    INFRASTRUCTURE = "infrastructure"
    DEVELOPMENT = "development"
    WELFARE = "welfare"
    EDUCATION = "education"
    HEALTH = "health"
    AGRICULTURE = "agriculture"
    OTHER = "other"


class DocumentType(str, Enum):
    CONCEPT_NOTE = "concept_note"
    DPR = "dpr"
    SUPPORTING_DOCUMENT = "supporting_document"
    FINANCIAL_DOCUMENT = "financial_document"
    TECHNICAL_DOCUMENT = "technical_document"
    OTHER = "other"


class ValidationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ActionType(str, Enum):
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_UPDATE = "document_update"
    DOCUMENT_DELETE = "document_delete"
    PROJECT_CREATE = "project_create"
    PROJECT_UPDATE = "project_update"
    CONCEPT_APPROVE = "concept_approve"
    CONCEPT_REJECT = "concept_reject"
    DPR_APPROVE = "dpr_approve"
    DPR_REJECT = "dpr_reject"
    FUND_RELEASE = "fund_release"
    COMMENT_ADD = "comment_add"