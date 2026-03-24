from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.auth import router as auth_router
from app.api.v1.assets import router as asset_router  # <-- Add this
from app.core.config import settings

app = FastAPI(
    title="ProofChain API",
    description="Decentralized document authentication and licensing",
    version="1.0.0"
)

# CORS for frontend (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(asset_router, prefix="/api/v1")  # <-- Register asset endpoints

@app.get("/health")
async def health_check():
    return {"status": "healthy", "network": settings.STELLAR_NETWORK}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)