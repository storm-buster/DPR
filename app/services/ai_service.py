import httpx
import asyncio
from typing import Dict, List, Optional
from ..core.config import settings
from ..models.enums import ValidationStatus


class AIValidationService:
    def __init__(self):
        self.base_url = settings.AI_SERVICE_URL
        self.api_key = settings.AI_SERVICE_API_KEY
        self.timeout = 300  # 5 minutes timeout for AI processing

    async def validate_document(
        self, 
        file_content: bytes, 
        filename: str, 
        document_type: str
    ) -> Dict:
        """
        Send document to AI service for validation
        Returns validation results including completeness score, missing fields, etc.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {
                    'file': (filename, file_content, 'application/octet-stream')
                }
                data = {
                    'document_type': document_type,
                    'api_key': self.api_key
                }
                
                response = await client.post(
                    f"{self.base_url}/validate",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    raise Exception(f"AI service returned status {response.status_code}: {response.text}")
                    
        except httpx.TimeoutException:
            raise Exception("AI validation service timeout")
        except Exception as e:
            raise Exception(f"AI validation failed: {str(e)}")

    async def generate_analytics_dashboard(
        self, 
        file_content: bytes, 
        filename: str, 
        document_type: str
    ) -> Dict:
        """
        Generate analytics dashboard for document
        Returns funding estimation, risk assessment, etc.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {
                    'file': (filename, file_content, 'application/octet-stream')
                }
                data = {
                    'document_type': document_type,
                    'api_key': self.api_key
                }
                
                response = await client.post(
                    f"{self.base_url}/generate-dashboard",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    raise Exception(f"AI service returned status {response.status_code}: {response.text}")
                    
        except httpx.TimeoutException:
            raise Exception("AI dashboard generation service timeout")
        except Exception as e:
            raise Exception(f"AI dashboard generation failed: {str(e)}")


class MockAIValidationService:
    """
    Mock AI service for development and testing
    Simulates AI validation responses
    """
    
    async def validate_document(
        self, 
        file_content: bytes, 
        filename: str, 
        document_type: str
    ) -> Dict:
        """Mock validation with realistic responses"""
        
        # Simulate processing time
        await asyncio.sleep(2)
        
        # Generate mock results based on document type and filename
        if document_type == "concept_note":
            return self._generate_concept_note_validation(filename)
        elif document_type == "dpr":
            return self._generate_dpr_validation(filename)
        else:
            return self._generate_generic_validation(filename)

    async def generate_analytics_dashboard(
        self, 
        file_content: bytes, 
        filename: str, 
        document_type: str
    ) -> Dict:
        """Mock analytics dashboard generation"""
        
        # Simulate processing time
        await asyncio.sleep(3)
        
        return {
            "funding_estimation": {
                "total_cost": 15000000,  # 1.5 crores
                "breakdown": {
                    "infrastructure": 8000000,
                    "equipment": 4000000,
                    "operational": 2000000,
                    "contingency": 1000000
                }
            },
            "risk_assessment": {
                "overall_risk": "medium",
                "risk_factors": [
                    "Weather dependency for construction",
                    "Land acquisition challenges",
                    "Regulatory approval timeline"
                ]
            },
            "timeline_analysis": {
                "estimated_duration": "18 months",
                "critical_milestones": [
                    "Environmental clearance - 3 months",
                    "Construction phase - 12 months",
                    "Testing and commissioning - 3 months"
                ]
            },
            "compliance_score": 85,
            "recommendations": [
                "Include detailed environmental impact assessment",
                "Add contingency planning for weather delays",
                "Consider phased implementation approach"
            ]
        }

    def _generate_concept_note_validation(self, filename: str) -> Dict:
        """Generate mock validation for concept note"""
        
        # Simulate different validation outcomes based on filename
        if "complete" in filename.lower():
            return {
                "completeness_score": 92.5,
                "missing_fields": [],
                "inconsistencies": [],
                "summary_report": "The concept note is well-structured and comprehensive. All mandatory sections are present with adequate detail. The project objectives are clearly defined and align with the proposed methodology.",
                "validation_status": "completed",
                "ai_model_version": "v2.1.0"
            }
        elif "incomplete" in filename.lower():
            return {
                "completeness_score": 65.0,
                "missing_fields": [
                    "Detailed budget breakdown is missing",
                    "Risk assessment section needs more detail",
                    "Stakeholder analysis is incomplete"
                ],
                "inconsistencies": [
                    "Timeline in executive summary doesn't match detailed schedule",
                    "Budget figures inconsistent between sections"
                ],
                "summary_report": "The concept note covers most essential elements but requires additional detail in several key areas. The project scope is well-defined, but financial and risk planning need strengthening.",
                "validation_status": "completed",
                "ai_model_version": "v2.1.0"
            }
        else:
            return {
                "completeness_score": 78.5,
                "missing_fields": [
                    "Environmental impact assessment details",
                    "Detailed implementation timeline"
                ],
                "inconsistencies": [],
                "summary_report": "The concept note provides a solid foundation for the project with clear objectives and methodology. Minor gaps in environmental considerations and timeline details should be addressed.",
                "validation_status": "completed",
                "ai_model_version": "v2.1.0"
            }

    def _generate_dpr_validation(self, filename: str) -> Dict:
        """Generate mock validation for DPR"""
        
        return {
            "completeness_score": 88.0,
            "missing_fields": [
                "Detailed technical specifications for equipment",
                "Quality assurance procedures"
            ],
            "inconsistencies": [
                "Cost estimates vary between technical and financial sections"
            ],
            "summary_report": "The DPR is comprehensive with detailed technical analysis and financial projections. The project design is well-thought-out with appropriate consideration of technical requirements and constraints.",
            "validation_status": "completed",
            "ai_model_version": "v2.1.0"
        }

    def _generate_generic_validation(self, filename: str) -> Dict:
        """Generate mock validation for other document types"""
        
        return {
            "completeness_score": 82.0,
            "missing_fields": [
                "Document version control information",
                "Approval signatures"
            ],
            "inconsistencies": [],
            "summary_report": "The document is well-structured and contains relevant information. Standard documentation practices should be followed for version control and approvals.",
            "validation_status": "completed",
            "ai_model_version": "v2.1.0"
        }


# Use mock service for development, real service for production
def get_ai_service():
    if settings.AI_SERVICE_URL == "http://localhost:8001":
        return MockAIValidationService()
    else:
        return AIValidationService()


# Global instance
ai_service = get_ai_service()