from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.user import User
from ..models.document import Document
from ..models.project import Project
from ..services.minio_service import minio_service

router = APIRouter(prefix="/document-comparison", tags=["document-comparison"])


@router.post("/compare")
async def compare_documents(
    document_ids: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compare multiple documents and return detailed analysis"""
    
    doc1_id = document_ids.get("document1_id")
    doc2_id = document_ids.get("document2_id")
    
    if not doc1_id or not doc2_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both document IDs are required"
        )
    
    # Get documents
    doc1 = db.query(Document).filter(Document.id == doc1_id).first()
    doc2 = db.query(Document).filter(Document.id == doc2_id).first()
    
    if not doc1 or not doc2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both documents not found"
        )
    
    # Check access permissions
    project1 = db.query(Project).filter(Project.id == doc1.project_id).first()
    project2 = db.query(Project).filter(Project.id == doc2.project_id).first()
    
    if (current_user.role == "state_user" and 
        (project1.created_by != current_user.id or project2.created_by != current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to compare these documents"
        )
    
    # Perform detailed comparison
    try:
        # Download both files for content analysis
        file1_content = await minio_service.download_file(doc1.file_path)
        file2_content = await minio_service.download_file(doc2.file_path)
        
        # Basic comparison metrics
        comparison_result = {
            "documents": {
                "document1": {
                    "id": str(doc1.id),
                    "filename": doc1.filename,
                    "version": doc1.version,
                    "size": doc1.file_size,
                    "uploaded_at": doc1.uploaded_at.isoformat(),
                    "hash": doc1.hash_id
                },
                "document2": {
                    "id": str(doc2.id),
                    "filename": doc2.filename,
                    "version": doc2.version,
                    "size": doc2.file_size,
                    "uploaded_at": doc2.uploaded_at.isoformat(),
                    "hash": doc2.hash_id
                }
            },
            "comparison_metrics": {
                "size_difference": doc2.file_size - doc1.file_size,
                "size_change_percentage": ((doc2.file_size - doc1.file_size) / doc1.file_size * 100) if doc1.file_size > 0 else 0,
                "content_identical": doc1.hash_id == doc2.hash_id,
                "version_gap": abs(doc2.version - doc1.version),
                "time_difference_hours": abs((doc2.uploaded_at - doc1.uploaded_at).total_seconds() / 3600)
            },
            "content_analysis": await _analyze_content_differences(file1_content, file2_content, doc1.filename, doc2.filename),
            "validation_comparison": _compare_validation_results(doc1, doc2)
        }
        
        return comparison_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare documents: {str(e)}"
        )


async def _analyze_content_differences(content1: bytes, content2: bytes, filename1: str, filename2: str) -> Dict:
    """Analyze content differences between two documents"""
    
    # Basic content analysis
    analysis = {
        "file_type_analysis": {
            "same_type": filename1.split('.')[-1].lower() == filename2.split('.')[-1].lower(),
            "file1_extension": filename1.split('.')[-1].lower(),
            "file2_extension": filename2.split('.')[-1].lower()
        },
        "content_metrics": {
            "byte_difference": len(content2) - len(content1),
            "similarity_score": _calculate_similarity_score(content1, content2)
        },
        "structural_changes": {
            "significant_changes": len(content2) != len(content1),
            "change_magnitude": "major" if abs(len(content2) - len(content1)) > len(content1) * 0.1 else "minor"
        }
    }
    
    # For text-based files, perform more detailed analysis
    if filename1.endswith(('.txt', '.md', '.csv')):
        try:
            text1 = content1.decode('utf-8')
            text2 = content2.decode('utf-8')
            analysis["text_analysis"] = _analyze_text_differences(text1, text2)
        except UnicodeDecodeError:
            analysis["text_analysis"] = {"error": "Unable to decode text content"}
    
    return analysis


def _calculate_similarity_score(content1: bytes, content2: bytes) -> float:
    """Calculate a basic similarity score between two byte arrays"""
    if len(content1) == 0 and len(content2) == 0:
        return 100.0
    
    if len(content1) == 0 or len(content2) == 0:
        return 0.0
    
    # Simple byte-level similarity
    min_len = min(len(content1), len(content2))
    max_len = max(len(content1), len(content2))
    
    matching_bytes = sum(1 for i in range(min_len) if content1[i] == content2[i])
    similarity = (matching_bytes / max_len) * 100
    
    return round(similarity, 2)


def _analyze_text_differences(text1: str, text2: str) -> Dict:
    """Analyze differences between two text documents"""
    
    lines1 = text1.splitlines()
    lines2 = text2.splitlines()
    
    return {
        "line_count_change": len(lines2) - len(lines1),
        "character_count_change": len(text2) - len(text1),
        "word_count_change": len(text2.split()) - len(text1.split()),
        "common_lines": len(set(lines1) & set(lines2)),
        "unique_lines_doc1": len(set(lines1) - set(lines2)),
        "unique_lines_doc2": len(set(lines2) - set(lines1))
    }


def _compare_validation_results(doc1: Document, doc2: Document) -> Dict:
    """Compare AI validation results between two documents"""
    
    comparison = {
        "both_validated": (doc1.ai_validation_results is not None and 
                          doc2.ai_validation_results is not None),
        "validation_status_change": None,
        "completeness_score_change": None,
        "issues_resolved": 0,
        "new_issues": 0
    }
    
    if doc1.ai_validation_results and doc2.ai_validation_results:
        score1 = doc1.ai_validation_results.get('completeness_score', 0)
        score2 = doc2.ai_validation_results.get('completeness_score', 0)
        
        comparison["completeness_score_change"] = score2 - score1
        
        missing1 = set(doc1.ai_validation_results.get('missing_fields', []))
        missing2 = set(doc2.ai_validation_results.get('missing_fields', []))
        
        comparison["issues_resolved"] = len(missing1 - missing2)
        comparison["new_issues"] = len(missing2 - missing1)
        
        inconsist1 = set(doc1.ai_validation_results.get('inconsistencies', []))
        inconsist2 = set(doc2.ai_validation_results.get('inconsistencies', []))
        
        comparison["inconsistencies_resolved"] = len(inconsist1 - inconsist2)
        comparison["new_inconsistencies"] = len(inconsist2 - inconsist1)
    
    return comparison