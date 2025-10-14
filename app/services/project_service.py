"""
Project service for MongoDB operations
"""
from typing import Optional, List
from beanie import PydanticObjectId
from ..models.project import Project
from ..models.enums import ProjectStatus, ProjectType


class ProjectService:
    """Service for project operations with MongoDB"""
    
    async def create_project(self, name: str, description: Optional[str], project_type: ProjectType,
                            department: str, state: str, created_by: str) -> Project:
        """Create a new project"""
        project = Project(
            name=name,
            description=description,
            project_type=project_type,
            department=department,
            state=state,
            created_by=created_by,
            status=ProjectStatus.DRAFT
        )
        
        try:
            # Save to MongoDB
            await project.insert()
            return project
        except Exception as e:
            # If MongoDB is not available, create a mock project with ID
            from datetime import datetime
            
            # Create a project-like object that can be returned
            project.id = PydanticObjectId()
            project.created_at = datetime.utcnow()
            project.updated_at = datetime.utcnow()
            
            print(f"⚠️ MongoDB not available, created mock project: {project.name}")
            return project
    
    async def get_project_by_id(self, project_id: str) -> Optional[Project]:
        """Get project by ID"""
        try:
            return await Project.get(PydanticObjectId(project_id))
        except:
            # Return None if database is not available
            return None
    
    async def get_projects_by_user(self, user_id: str) -> List[Project]:
        """Get all projects created by a user"""
        try:
            return await Project.find(Project.created_by == user_id).to_list()
        except:
            # Return empty list if database is not available
            return []
    
    async def get_all_projects(self) -> List[Project]:
        """Get all projects"""
        try:
            return await Project.find_all().to_list()
        except:
            # Return empty list if database is not available
            return []
    
    async def get_projects_by_status(self, status: ProjectStatus) -> List[Project]:
        """Get projects by status"""
        try:
            return await Project.find(Project.status == status).to_list()
        except:
            # Return empty list if database is not available
            return []
    
    async def get_projects_by_statuses(self, statuses: List[ProjectStatus]) -> List[Project]:
        """Get projects by multiple statuses"""
        try:
            return await Project.find({"status": {"$in": statuses}}).to_list()
        except:
            # Return empty list if database is not available
            return []
    
    async def update_project(self, project_id: str, **kwargs) -> Optional[Project]:
        """Update project"""
        try:
            project = await Project.get(PydanticObjectId(project_id))
            if not project:
                return None
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(project, key):
                    setattr(project, key, value)
            
            await project.save()
            return project
        except:
            return None
    
    async def delete_project(self, project_id: str) -> bool:
        """Delete project"""
        try:
            project = await Project.get(PydanticObjectId(project_id))
            if project:
                await project.delete()
                return True
            return False
        except:
            return False
    
    async def filter_projects(self, user_id: Optional[str] = None, status: Optional[ProjectStatus] = None,
                             project_type: Optional[ProjectType] = None, department: Optional[str] = None,
                             state: Optional[str] = None, search: Optional[str] = None) -> List[Project]:
        """Filter projects based on criteria"""
        try:
            query = {}
            
            # Filter by user (for state users)
            if user_id:
                query["created_by"] = user_id
            
            # Filter by status
            if status:
                query["status"] = status
            
            # Filter by project type
            if project_type:
                query["project_type"] = project_type
            
            # Filter by department
            if department:
                query["department"] = department
            
            # Filter by state
            if state:
                query["state"] = state
            
            # Filter by search term
            if search:
                query["$or"] = [
                    {"name": {"$regex": search, "$options": "i"}},
                    {"description": {"$regex": search, "$options": "i"}}
                ]
            
            # Get projects and sort by created_at descending
            projects = await Project.find(query).sort(-Project.created_at).to_list()
            
            return projects
        except:
            # Return empty list if database is not available
            return []


# Global project service instance
project_service = ProjectService()