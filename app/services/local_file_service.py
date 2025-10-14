import hashlib
import uuid
import os
from datetime import datetime
from typing import BinaryIO, Optional
from pathlib import Path

class LocalFileService:
    """Local file storage service for development/testing"""
    
    def __init__(self):
        self.storage_path = Path("./file_storage")
        self.storage_path.mkdir(exist_ok=True)
    
    def generate_file_hash(self, file_data: bytes) -> str:
        """Generate SHA-256 hash of file content"""
        return hashlib.sha256(file_data).hexdigest()
    
    def generate_file_path(self, project_id: str, filename: str, document_type: str) -> str:
        """Generate unique file path for storage"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = filename.replace(" ", "_").replace("/", "_")
        return f"projects/{project_id}/{document_type}/{timestamp}_{unique_id}_{safe_filename}"
    
    async def upload_file(
        self, 
        file_data: bytes, 
        file_path: str, 
        content_type: str
    ) -> tuple[str, str]:
        """
        Upload file to local storage and return file path and hash
        Returns: (file_path, file_hash)
        """
        try:
            # Generate file hash
            file_hash = self.generate_file_hash(file_data)
            
            # Create directory structure
            full_path = self.storage_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(full_path, 'wb') as f:
                f.write(file_data)
            
            return file_path, file_hash
            
        except Exception as e:
            raise Exception(f"Failed to upload file: {str(e)}")
    
    async def download_file(self, file_path: str) -> bytes:
        """Download file from local storage"""
        try:
            full_path = self.storage_path / file_path
            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            with open(full_path, 'rb') as f:
                return f.read()
                
        except Exception as e:
            raise Exception(f"Failed to download file: {str(e)}")
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from local storage"""
        try:
            full_path = self.storage_path / file_path
            if full_path.exists():
                full_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Failed to delete file: {str(e)}")
            return False
    
    def get_file_url(self, file_path: str, expires_in_seconds: int = 3600) -> str:
        """Generate URL for file access (local path for development)"""
        return f"/files/{file_path}"

# Global instance for local development
local_file_service = LocalFileService()