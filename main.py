from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time

from app.core.config import settings
from app.services.user_service import user_service
from app.models.enums import UserRole
from app.api.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize MongoDB database
    print("🚀 Initializing MongoDB database...")
    try:
        from app.core.database import init_database
        await init_database()
        print("✅ MongoDB connection established")
        
        # Create test users if database is available
        from app.core.database import get_database
        database = get_database()
        
        if database:
            from app.models.user import User
            from app.models.enums import UserRole
            from app.core.security import get_password_hash
            
            try:
                # Check if users already exist
                state_user = await User.find_one({"username": "state_user"})
                if not state_user:
                    state_user = User(
                        username="state_user",
                        email="state@example.com",
                        password_hash=get_password_hash("password123"),
                        role=UserRole.STATE_USER,
                        department="Roads",
                        state="Maharashtra"
                    )
                    await state_user.insert()
                    print("✅ Created State user")
                
                mdoner_user = await User.find_one({"username": "mdoner_user"})
                if not mdoner_user:
                    mdoner_user = User(
                        username="mdoner_user",
                        email="mdoner@example.com",
                        password_hash=get_password_hash("password123"),
                        role=UserRole.MDONER_USER
                    )
                    await mdoner_user.insert()
                    print("✅ Created MDONER user")
                
                # Create sample projects if they don't exist
                from app.models.project import Project
                from app.models.enums import ProjectType, ProjectStatus
                
                existing_projects = await Project.find().to_list()
                if not existing_projects:
                    # Sample project 1 - Draft
                    project1 = Project(
                        name="Highway Expansion Project",
                        description="Expansion of NH-48 from 4-lane to 6-lane highway",
                        project_type=ProjectType.INFRASTRUCTURE,
                        department="Roads",
                        state="Maharashtra",
                        created_by=str(state_user.id)
                    )
                    await project1.insert()
                    
                    # Sample project 2 - Concept Submitted
                    project2 = Project(
                        name="Rural Water Supply Scheme",
                        description="Providing clean water access to 50 villages",
                        project_type=ProjectType.DEVELOPMENT,
                        department="Water Resources",
                        state="Maharashtra",
                        created_by=str(state_user.id),
                        status=ProjectStatus.CONCEPT_SUBMITTED
                    )
                    await project2.insert()
                    
                    # Sample project 3 - Concept Approved
                    project3 = Project(
                        name="Primary School Infrastructure",
                        description="Building new classrooms and facilities",
                        project_type=ProjectType.EDUCATION,
                        department="Education",
                        state="Maharashtra",
                        created_by=str(state_user.id),
                        status=ProjectStatus.CONCEPT_APPROVED,
                        concept_note_approved=True
                    )
                    await project3.insert()
                    
                    print("✅ Sample projects created successfully")
                    
            except Exception as e:
                print(f"⚠️ Error creating test data: {e}")
        else:
            print("⚠️ Database not available - skipping test data creation")
        
        print("📝 Test Credentials:")
        print("State User - Username: state_user, Password: password123")
        print("MDONER User - Username: mdoner_user, Password: password123")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise
    
    yield
    
    # Cleanup
    try:
        from app.core.database import close_database
        await close_database()
        print("✅ MongoDB connection closed")
    except Exception as e:
        print(f"⚠️ Error closing database: {e}")


app = FastAPI(
    title="Government Project Platform API",
    description="API for government project submission and monitoring platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include routers
app.include_router(auth_router, prefix="/api")

# Import projects router
from app.api.projects import router as projects_router
app.include_router(projects_router, prefix="/api")

# Import notifications router
from app.api.notifications import router as notifications_router
app.include_router(notifications_router, prefix="/api")

# Import AI router
from app.api.ai import router as ai_router
app.include_router(ai_router, prefix="/api")

# Import documents router
from app.api.documents import router as documents_router
app.include_router(documents_router, prefix="/api")

# Import projects router (additional routes)
from app.api.projects import router as projects_router_additional
# Note: projects_router is already included above, this adds additional routes

# Import comments router - temporarily disabled during MongoDB migration
# from app.api.comments import router as comments_router
# app.include_router(comments_router, prefix="/api")


@app.get("/")
def root():
    return {"message": "Government Project Platform API - In-Memory Mode"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "mode": "in-memory"}