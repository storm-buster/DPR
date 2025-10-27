from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time

from app.core.config import settings
# from app.services.user_service import user_service  # Disabled - uses MongoDB
from app.models.enums import UserRole
from app.api.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Skip MongoDB - using in-memory storage only
    print("🚀 Starting backend in in-memory mode...")
    try:
        
        # Create test users in memory
        database = None
        
        if False:  # Skip MongoDB user creation
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
                        department="Public Works Department",
                        state="Arunachal Pradesh"
                    )
                    await state_user.insert()
                    print("✅ Created State user (Arunachal Pradesh)")
                
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
                    # Sample project 1 - Trans-Arunachal Highway
                    project1 = Project(
                        name="Trans-Arunachal Highway Development",
                        description="Construction of 85km all-weather highway connecting remote villages in Tawang district",
                        project_type=ProjectType.INFRASTRUCTURE,
                        department="Public Works Department",
                        state="Arunachal Pradesh",
                        created_by=str(state_user.id)
                    )
                    await project1.insert()
                    
                    # Sample project 2 - Healthcare Center
                    project2 = Project(
                        name="Integrated Healthcare Center - Itanagar",
                        description="Establishment of 100-bed integrated healthcare facility with modern equipment",
                        project_type=ProjectType.HEALTH,
                        department="Health & Family Welfare",
                        state="Arunachal Pradesh",
                        created_by=str(state_user.id),
                        status=ProjectStatus.CONCEPT_SUBMITTED
                    )
                    await project2.insert()
                    
                    # Sample project 3 - Skill Development
                    project3 = Project(
                        name="Skill Development Center - Pasighat",
                        description="Multi-skill training center for youth employment in tourism and handicrafts",
                        project_type=ProjectType.EDUCATION,
                        department="Skill Development",
                        state="Arunachal Pradesh",
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
        print(f"⚠️ Startup warning: {e}")
        # Don't raise - continue without MongoDB
    
    print("✅ Backend started successfully in in-memory mode")
    
    yield
    
    # Cleanup
    print("✅ Backend shutdown")


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