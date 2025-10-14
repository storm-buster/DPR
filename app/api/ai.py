from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File
from typing import Dict, Optional
import asyncio

from ..core.deps import get_current_user
from ..models.user import User
from ..models.document import Document
from ..models.ai_validation_result import AIValidationResult
from ..models.enums import ValidationStatus
from ..services.gemini_service_simple import simple_gemini_service, analyze_pdf_document, validate_pdf_document, generate_summary
from ..services.document_service import document_service

router = APIRouter(prefix="/ai", tags=["ai"])


async def process_document_validation(document_id: str, pdf_bytes: bytes):
    """Background task to process AI validation using Gemini RAG"""
    try:
        # Get document from in-memory storage
        document = document_service.get_document_by_id(document_id)
        if not document:
            return

        # Update status to in_progress
        document_service.update_document(document_id, ai_validation_status=ValidationStatus.IN_PROGRESS)

        # Use Gemini RAG for validation
        validation_results = await validate_pdf_document(pdf_bytes)

        # Create AI validation result
        ai_result = AIValidationResult(
            document_id=document_id,
            completeness_score=validation_results.get('completeness_score', 0),
            missing_fields=validation_results.get('missing_sections', []),
            inconsistencies=validation_results.get('recommendations', []),
            summary_report=validation_results.get('compliance_status', ''),
            ai_model_version='gemini-1.5-pro',
            detailed_analysis=validation_results
        )

        # Store AI result in memory (using document service db)
        from ..core.database import get_db
        db = get_db()
        db.ai_results[ai_result.id] = ai_result

        # Update document status and results
        document_service.update_document(
            document_id,
            ai_validation_status=ValidationStatus.COMPLETED,
            ai_validation_results=validation_results,
            validation_result_id=ai_result.id
        )

    except Exception as e:
        # Update status to failed
        document_service.update_document(
            document_id,
            ai_validation_status=ValidationStatus.FAILED,
            ai_validation_results={
                "error": str(e),
                "validation_status": "failed"
            }
        )


@router.post("/analyze-pdf")
async def analyze_pdf_upload(
    file: UploadFile = File(...),
    analysis_type: str = "analysis",
    current_user: User = Depends(get_current_user)
):
    """Analyze uploaded PDF using Gemini RAG (supports 300-400 page documents)"""
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    # Read file content
    pdf_bytes = await file.read()
    
    # Validate file size (max 50MB for large documents)
    if len(pdf_bytes) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size too large. Maximum 50MB allowed."
        )
    
    try:
        if analysis_type == "validation":
            results = await validate_pdf_document(pdf_bytes)
        else:
            results = await analyze_pdf_document(pdf_bytes)
        
        return {
            "status": "success",
            "filename": file.filename,
            "analysis_type": analysis_type,
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/analyze-text")
async def analyze_text_content(
    content: Dict[str, str],
    current_user: User = Depends(get_current_user)
):
    """Analyze text content using Gemini (multilingual support)"""
    
    text_content = content.get('text', '')
    if not text_content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text content is required"
        )
    
    try:
        results = await generate_summary(text_content)
        
        return {
            "status": "success",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/validate/{document_id}")
async def trigger_document_validation(
    document_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Trigger AI validation for a stored document"""
    
    # Get document and verify access
    document = document_service.get_document_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Check if user has access to the document
    from ..services.project_service import project_service
    project = project_service.get_project_by_id(document.project_id)
    if (current_user.role == "state_user" and 
        project.created_by != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to validate this document"
        )

    # Check if validation is already in progress
    if document.ai_validation_status == ValidationStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Validation already in progress"
        )

    # For now, return a placeholder since we don't have actual file storage
    # In real implementation, you would download the file and process it
    return {
        "message": "AI validation would be started for stored document",
        "document_id": document_id,
        "note": "Use /analyze-pdf endpoint for direct PDF analysis"
    }


@router.get("/validation-results/{document_id}")
def get_validation_results(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get AI validation results for a document"""
    
    # Get document and verify access
    document = document_service.get_document_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Check if user has access to the document
    from ..services.project_service import project_service
    project = project_service.get_project_by_id(document.project_id)
    if (current_user.role == "state_user" and 
        project.created_by != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view validation results"
        )

    # Get validation result
    validation_result = None
    if document.validation_result_id:
        from ..core.database import get_db
        db = get_db()
        validation_result = db.ai_results.get(document.validation_result_id)

    if not validation_result:
        return {
            "status": document.ai_validation_status,
            "message": "No validation results available"
        }

    return {
        "status": document.ai_validation_status,
        "completeness_score": validation_result.completeness_score,
        "missing_fields": validation_result.missing_fields,
        "inconsistencies": validation_result.inconsistencies,
        "summary_report": validation_result.summary_report,
        "validation_timestamp": validation_result.validation_timestamp,
        "ai_model_version": validation_result.ai_model_version,
        "detailed_analysis": validation_result.detailed_analysis
    }


@router.post("/generate-dashboard-pdf")
async def generate_dashboard_from_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Generate analytics dashboard from uploaded PDF (MDONER users only)"""
    
    # Only MDONER users can generate dashboards
    if current_user.role != "mdoner_user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only MDONER users can generate analytics dashboards"
        )

    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    # Read file content
    pdf_bytes = await file.read()
    
    try:
        # Analyze document for dashboard generation
        analysis_results = await analyze_pdf_document(pdf_bytes)
        
        # Generate dashboard data from analysis
        dashboard_data = {
            "project_overview": {
                "name": analysis_results.get('project_details', {}).get('name', 'Unknown Project'),
                "location": analysis_results.get('project_details', {}).get('location', 'Not specified'),
                "cost": analysis_results.get('project_details', {}).get('cost', 'Not specified'),
                "duration": analysis_results.get('project_details', {}).get('duration', 'Not specified')
            },
            "financial_analysis": {
                "total_cost": analysis_results.get('financial_breakdown', {}),
                "cost_breakdown": analysis_results.get('technical_specs', [])
            },
            "risk_assessment": {
                "identified_risks": analysis_results.get('risks', []),
                "mitigation_strategies": analysis_results.get('benefits', [])
            },
            "compliance_status": {
                "overall_status": analysis_results.get('compliance', {}),
                "language": analysis_results.get('language', 'english')
            },
            "ai_insights": {
                "summary": analysis_results.get('summary', ''),
                "recommendations": analysis_results.get('benefits', [])
            },
            "metadata": analysis_results.get('metadata', {})
        }
        
        return {
            "status": "success",
            "filename": file.filename,
            "dashboard": dashboard_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dashboard generation failed: {str(e)}"
        )


@router.get("/languages")
def get_supported_languages():
    """Get list of supported languages for multilingual analysis"""
    return {
        "supported_languages": [
            {
                "code": "english",
                "name": "English",
                "native_name": "English"
            },
            {
                "code": "hindi", 
                "name": "Hindi",
                "native_name": "हिन्दी"
            },
            {
                "code": "assamese",
                "name": "Assamese", 
                "native_name": "অসমীয়া"
            }
        ],
        "default_language": "english",
        "auto_detection": True
    }


@router.post("/test-rag")
async def test_rag_analysis(
    current_user: User = Depends(get_current_user)
):
    """Test RAG analysis with sample document (for development/testing)"""
    
    # Sample test document (from your example)
    test_text = """PROJECT DETAILED REPORT
CHAPTER 1: INTRODUCTION
Project Name: Construction of 2-Lane Road in Tawang District
Location: Tawang, Arunachal Pradesh
Implementing Agency: Ministry of Development of North Eastern Region

CHAPTER 2: PROJECT BACKGROUND
The project aims to construct a 45 km two-lane road connecting Village A to Town B in the Tawang District.
This region currently lacks proper road connectivity, affecting economic development and access to essential services.
The proposed road will serve over 50,000 residents and facilitate tourism in this scenic region.

CHAPTER 3: TECHNICAL SPECIFICATIONS
Road Length: 45 kilometers
Road Width: 7 meters (two-lane)
Number of Bridges: 3 major bridges
Number of Culverts: 15 culverts
Pavement Type: Bituminous concrete
Design Speed: 60 km/h

CHAPTER 4: FINANCIAL DETAILS
Total Project Cost: Rs. 250 Crores
Breakdown:
- Civil Works: Rs. 180 Crores
- Bridges and Culverts: Rs. 50 Crores
- Land Acquisition: Rs. 10 Crores
- Contingencies: Rs. 10 Crores

CHAPTER 5: PROJECT TIMELINE
Total Duration: 36 months
Phase 1 (Months 1-12): Land acquisition and site preparation
Phase 2 (Months 13-30): Main construction work
Phase 3 (Months 31-36): Finishing and quality checks

CHAPTER 6: ENVIRONMENTAL IMPACT
Environmental clearance obtained from State Environmental Impact Assessment Authority.
Mitigation measures include:
- Tree plantation along the road
- Proper drainage systems
- Wildlife crossing provisions

CHAPTER 7: SOCIAL IMPACT
Expected Benefits:
- Improved connectivity for 50,000+ residents
- Enhanced access to healthcare and education
- Boost to local tourism industry
- Creation of 500+ temporary jobs during construction
- Improved market access for local farmers

CHAPTER 8: RISK ASSESSMENT
Key Risks Identified:
1. Weather-related delays during monsoon season
2. Potential cost escalation due to terrain challenges
3. Land acquisition delays
4. Availability of skilled labor in remote location

Mitigation Strategies:
- Seasonal work planning
- Contingency budget allocation
- Early stakeholder engagement
- Training programs for local workforce

CHAPTER 9: IMPLEMENTATION PLAN
The project will be implemented through competitive bidding.
Quality control measures will be strictly enforced.
Regular monitoring and evaluation will be conducted.

CHAPTER 10: CONCLUSION
This project is critical for the development of the Tawang region and will significantly improve
the quality of life for residents while promoting economic growth and tourism.""" * 3  # Repeat to make it longer
    
    try:
        results = await generate_summary(test_text)
        
        return {
            "status": "success",
            "test_document_length": len(test_text),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test analysis failed: {str(e)}"
        )