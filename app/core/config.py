from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database - MongoDB
    MONGODB_URL: str = "mongodb+srv://sterben:Avinash%40123@cluster1.nkxlyxt.mongodb.net/dpr_system?retryWrites=true&w=majority&appName=Cluster1"
    DATABASE_NAME: str = "dpr_system"
    
    # MinIO - Disabled for local testing
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET_NAME: str = "documents"
    MINIO_SECURE: bool = False
    
    # JWT
    SECRET_KEY: str = "development-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "*"]
    
    # AI Service - Gemini Integration
    GEMINI_API_KEY: str = "AIzaSyCf8PZ4jxCYXHM4cTq8U4nAzKMFfCvTbIo"
    AI_SERVICE_URL: str = "http://localhost:8001"
    AI_SERVICE_API_KEY: str = "test-api-key"
    
    class Config:
        env_file = ".env"


settings = Settings()