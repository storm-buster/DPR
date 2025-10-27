from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create a simple FastAPI app without lifespan for Vercel
app = FastAPI(title="SameekshaAI API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from app.api.auth import router as auth_router
from app.api.ai import router as ai_router

app.include_router(auth_router, prefix="/api")
app.include_router(ai_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "SameekshaAI API - Vercel Deployment"}

@app.get("/health")
def health():
    return {"status": "healthy", "mode": "serverless"}

# Vercel handler
handler = app
