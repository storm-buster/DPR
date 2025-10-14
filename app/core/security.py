from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
import hashlib
from fastapi import HTTPException, status
from .config import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using simple SHA-256 hashing (for development only)"""
    return get_password_hash(plain_password) == hashed_password


def get_password_hash(password: str) -> str:
    """Hash password using SHA-256 (for development only - use bcrypt in production)"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )