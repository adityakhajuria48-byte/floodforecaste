"""API module: satellite.py"""
from fastapi import APIRouter

router = APIRouter()

# Placeholder - actual implementation will be added
@router.get("/")
async def list_endpoints():
    return {"module": "satellite.py", "status": "ok"}
