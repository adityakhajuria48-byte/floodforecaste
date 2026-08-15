"""API module: location.py - Location search and geocoding services"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import httpx

router = APIRouter()

class LocationQuery(BaseModel):
    query: str
    limit: int = 10

class LocationResult(BaseModel):
    name: str
    display_name: str
    lat: float
    lon: float
    type: str
    bounding_box: Optional[dict] = None

@router.post("/search", response_model=List[LocationResult])
async def search_locations(query: LocationQuery):
    """Search for locations using Nominatim (OpenStreetMap)"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": query.query,
                    "format": "json",
                    "limit": query.limit,
                    "addressdetails": 1,
                },
                headers={"User-Agent": "FloodPredictionSystem/1.0"}
            )
            response.raise_for_status()
            results = response.json()
            
            return [
                LocationResult(
                    name=item.get("name", ""),
                    display_name=item.get("display_name", ""),
                    lat=float(item.get("lat", 0)),
                    lon=float(item.get("lon", 0)),
                    type=item.get("type", "unknown"),
                    bounding_box=None  # Can be populated from bbox if available
                )
                for item in results
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Location search failed: {str(e)}")

@router.post("/reverse")
async def reverse_geocode(lat: float, lng: float):
    """Reverse geocoding - get address from coordinates"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={
                    "lat": lat,
                    "lon": lng,
                    "format": "json",
                },
                headers={"User-Agent": "FloodPredictionSystem/1.0"}
            )
            response.raise_for_status()
            result = response.json()
            return {
                "display_name": result.get("display_name", ""),
                "address": result.get("address", {}),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reverse geocoding failed: {str(e)}")

@router.get("/")
async def list_endpoints():
    return {"module": "location.py", "endpoints": ["/search", "/reverse"]}
