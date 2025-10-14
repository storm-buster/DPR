"""
User service for MongoDB operations with fallback support
"""
from typing import Optional, List
from beanie import PydanticObjectId
from ..models.user import User
from ..models.enums import UserRole
from ..core.security import get_password_hash
from datetime import datetime


class UserService:
    """Service for user operations with MongoDB"""
    
    def __init__(self):
        # In-memory fallback users when MongoDB is not available
        self.fallback_users = {
            "state_user": {
                "id": "507f1f77bcf86cd799439011",
                "username": "state_user",
                "email": "state@example.com",
                "password_hash": get_password_hash("password123"),
                "role": UserRole.STATE_USER,
                "department": "Roads",
                "state": "Maharashtra",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            "mdoner_user": {
                "id": "507f1f77bcf86cd799439012",
                "username": "mdoner_user",
                "email": "mdoner@example.com",
                "password_hash": get_password_hash("password123"),
                "role": UserRole.MDONER_USER,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    
    async def create_user(self, username: str, email: str, password: str, role: str, 
                         department: Optional[str] = None, state: Optional[str] = None) -> User:
        """Create a new user"""
        try:
            # Check if user already exists
            existing_user = await User.find_one(
                {"$or": [{"username": username}, {"email": email}]}
            )
            if existing_user:
                raise ValueError("Username or email already exists")
            
            # Create user
            user = User(
                username=username,
                email=email,
                password_hash=get_password_hash(password),
                role=role,
                department=department,
                state=state
            )
            
            # Save to MongoDB
            await user.insert()
            return user
        except Exception as e:
            print(f"⚠️ MongoDB not available for user creation: {e}")
            raise ValueError("Database not available")
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            return await User.get(PydanticObjectId(user_id))
        except:
            # Fallback: return test users when DB is not available
            for user_data in self.fallback_users.values():
                if user_data["id"] == user_id:
                    return self._create_fallback_user(user_data)
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            return await User.find_one(User.username == username)
        except:
            # Fallback: return test users when DB is not available
            if username in self.fallback_users:
                user_data = self.fallback_users[username]
                return self._create_fallback_user(user_data)
            return None
    
    def _create_fallback_user(self, user_data: dict):
        """Create a fallback user object that mimics the User model"""
        class FallbackUser:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)
        
        return FallbackUser(user_data)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            return await User.find_one(User.email == email)
        except:
            # Fallback: check test users
            for user_data in self.fallback_users.values():
                if user_data["email"] == email:
                    return self._create_fallback_user(user_data)
            return None
    
    async def get_all_users(self) -> List[User]:
        """Get all users"""
        try:
            return await User.find_all().to_list()
        except:
            # Return fallback users
            return [self._create_fallback_user(data) for data in self.fallback_users.values()]
    
    async def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """Update user"""
        try:
            user = await User.get(PydanticObjectId(user_id))
            if not user:
                return None
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            await user.save()
            return user
        except:
            return None
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        try:
            user = await User.get(PydanticObjectId(user_id))
            if user:
                await user.delete()
                return True
            return False
        except:
            return False


# Global user service instance
user_service = UserService()