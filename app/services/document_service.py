"""
Document service for MongoDB operations
"""
from typing import Optional, List
from beanie import PydanticObjectId
from ..models.document import Document
from ..models.enums import DocumentType, ValidationStatus


class DocumentService:
    """Service for document operations with MongoDB"""
    
    async def create_document(self, project_id: str, filename: str, document_type: DocumentType,
                             file_path: str, file_size: int, mime_type: str, hash_id: str,
                             uploaded_by: str) -> Document:
        """Create a new document"""
        document = Document(
            project_id=project_id,
            filename=filename,
            document_type=document_type,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            hash_id=hash_id,
            uploaded_by=uploaded_by
        )
        
        # Save to MongoDB
        await document.insert()
        return document
    
    async def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """Get document by ID"""
        try:
            return await Document.get(PydanticObjectId(document_id))
        except:
            return None
    
    async def get_documents_by_project(self, project_id: str) -> List[Document]:
        """Get all documents for a project"""
        return await Document.find(Document.project_id == project_id).to_list()
    
    async def update_document(self, document_id: str, **kwargs) -> Optional[Document]:
        """Update document"""
        try:
            document = await Document.get(PydanticObjectId(document_id))
            if not document:
                return None
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(document, key):
                    setattr(document, key, value)
            
            await document.save()
            return document
        except:
            return None
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete document"""
        try:
            document = await Document.get(PydanticObjectId(document_id))
            if document:
                await document.delete()
                return True
            return False
        except:
            return False


# Global document service instance
document_service = DocumentService()