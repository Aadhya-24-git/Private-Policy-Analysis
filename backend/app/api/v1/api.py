from fastapi import APIRouter
from app.api.v1.endpoints import health, analyze, chat, audit, compare

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(analyze.router, tags=["Analysis"])
api_router.include_router(chat.router, tags=["Interactive Auditor"])
api_router.include_router(audit.router, tags=["Risk Audit"])
api_router.include_router(compare.router, tags=["Policy Comparison"])



