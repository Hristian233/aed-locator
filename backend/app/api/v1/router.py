from fastapi import APIRouter

from app.api.v1 import admin, aeds, auth

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(aeds.router)
api_router.include_router(admin.router)
