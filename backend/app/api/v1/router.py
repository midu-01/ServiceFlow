from fastapi import APIRouter
from app.api.v1.endpoints import auth, service_requests, websocket

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth.router)
api_v1_router.include_router(service_requests.router)
api_v1_router.include_router(websocket.router)
