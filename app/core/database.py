import motor.motor_asyncio
from beanie import init_beanie
from .config import settings

# MongoDB client
client = None
database = None

async def init_database():
    """Initialize MongoDB connection and Beanie ODM"""
    global client, database
    
    try:
        # Replace password placeholder with actual password
        mongodb_url = settings.MONGODB_URL.replace("<db_password>", "yourpassword")
        print(f"🔗 Connecting to MongoDB: {mongodb_url}")
        
        client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_url)
        database = client[settings.DATABASE_NAME]
        
        # Import all document models
        from ..models.user import User
        from ..models.project import Project
        from ..models.document import Document
        from ..models.comment import Comment
        from ..models.notification import Notification
        from ..models.audit_log import AuditLog
        from ..models.ai_validation_result import AIValidationResult
        
        # Initialize Beanie with document models
        await init_beanie(
            database=database,
            document_models=[
                User,
                Project, 
                Document,
                Comment,
                Notification,
                AuditLog,
                AIValidationResult
            ]
        )
        
        print("✅ MongoDB connection established successfully")
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("⚠️ Running without database - some features will not work")
        # Set database to None so services can handle gracefully
        database = None

async def close_database():
    """Close MongoDB connection"""
    global client
    if client:
        client.close()

def get_database():
    """Get MongoDB database instance"""
    return database