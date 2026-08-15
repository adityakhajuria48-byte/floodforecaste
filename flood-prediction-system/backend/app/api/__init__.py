"""API module: __init__.py"""
from fastapi import APIRouter

router = APIRouter()

# Placeholder - actual implementation will be added
@router.get("/")
async def list_endpoints():
    return {"module": "__init__.py", "status": "ok"}
