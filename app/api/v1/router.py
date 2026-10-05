from fastapi import APIRouter

from app.api.v1.endpoints import addresses

api_router = APIRouter()

api_router.include_router(addresses.router)
