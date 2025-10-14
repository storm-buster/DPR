from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from ..models.enums import UserRole


class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole
    department: Optional[str] = None
    state: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse