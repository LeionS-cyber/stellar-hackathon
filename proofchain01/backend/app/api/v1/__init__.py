"""API v1 module"""

from fastapi import APIRouter
from app.api.v1 import auth, assets, licenses

router = APIRouter(prefix="/api/v1")

# Include routers
router.include_router(auth.router)
router.include_router(assets.router)
router.include_router(licenses.router)

__all__ = ["router"]