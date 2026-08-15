"""
Satellite data acquisition service for Sentinel-1 and Sentinel-2 imagery.
Interfaces with Copernicus Data Space Ecosystem API.
"""
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from app.core.config import settings


class CopernicusClient:
    """Client for Copernicus Data Space Ecosystem API"""
    
    BASE_URL = "https://catalogue.dataspace.copernicus.eu"
    AUTH_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    
    def __init__(self):
        self.username = settings.COPEERNICUS_USERNAME
        self.password = settings.COPEERNICUS_PASSWORD
        self.access_token = None
        self.token_expires_at = None
    
    async def authenticate(self) -> str:
        """Authenticate with Copernicus Data Space and get access token"""
        if not self.username or not self.password:
            raise ValueError("Copernicus credentials not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.AUTH_URL,
                data={
                    "grant_type": "password",
                    "username": self.username,
                    "password": self.password,
                    "client_id": "cdse-public",
                },
            )
            response.raise_for_status()
            tokens = response.json()
            self.access_token = tokens["access_token"]
            # Token expires in typically 3600 seconds
            self.token_expires_at = datetime.now().timestamp() + tokens.get("expires_in", 3600)
            return self.access_token
    
    async def _get_token(self) -> str:
        """Get valid access token, refreshing if necessary"""
        if not self.access_token or not self.token_expires_at or datetime.now().timestamp() >= self.token_expires_at:
            await self.authenticate()
        return self.access_token
    
    async def search_sentinel1(
        self,
        aoi_bbox: List[float],
        start_date: str,
        end_date: str,
        polarization: str = "VV+VH",
        product_type: str = "GRD",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Search for Sentinel-1 GRD products"""
        token = await self._get_token()
        
        # Build OData filter
        date_filter = f"ContentDate/Start ge {start_date}T00:00:00Z and ContentDate/Start le {end_date}T23:59:59Z"
        bbox_filter = f"OGeoRed.B0.Intersects(geo'SRID=4326;POLYGON(({aoi_bbox[0]} {aoi_bbox[1]},{aoi_bbox[2]} {aoi_bbox[1]},{aoi_bbox[2]} {aoi_bbox[3]},{aoi_bbox[0]} {aoi_bbox[3]},{aoi_bbox[0]} {aoi_bbox[1]}))')"
        platform_filter = "Collection/Name eq 'SENTINEL-1'"
        product_filter = f"ProductType eq '{product_type}'"
        
        odata_filter = f"{date_filter} and {bbox_filter} and {platform_filter} and {product_filter}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/resto/api/collections/Sentinel1/search.json",
                params={
                    "$filter": odata_filter,
                    "$top": limit,
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            results = response.json()
            
            scenes = []
            for feature in results.get("features", []):
                props = feature.get("properties", {})
                scenes.append({
                    "id": feature.get("id", ""),
                    "platform": "Sentinel-1",
                    "acquisition_date": props.get("completionTime", ""),
                    "polarization": props.get("polarizationChannels", polarization),
                    "product_type": product_type,
                    "url": self._get_download_url(feature),
                    "bounds": self._extract_bounds(feature),
                    "cloud_cover": None,  # SAR doesn't have cloud cover
                })
            
            return scenes
    
    async def search_sentinel2(
        self,
        aoi_bbox: List[float],
        start_date: str,
        end_date: str,
        product_level: str = "L2A",
        max_cloud_cover: float = 20.0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Search for Sentinel-2 products"""
        token = await self._get_token()
        
        # Build OData filter
        date_filter = f"ContentDate/Start ge {start_date}T00:00:00Z and ContentDate/Start le {end_date}T23:59:59Z"
        bbox_filter = f"OGeoRed.B0.Intersects(geo'SRID=4326;POLYGON(({aoi_bbox[0]} {aoi_bbox[1]},{aoi_bbox[2]} {aoi_bbox[1]},{aoi_bbox[2]} {aoi_bbox[3]},{aoi_bbox[0]} {aoi_bbox[3]},{aoi_bbox[0]} {aoi_bbox[1]}))')"
        platform_filter = "Collection/Name eq 'SENTINEL-2'"
        product_filter = f"ProductType eq '{product_level}'"
        cloud_filter = f"CloudCover ge 0 and CloudCover le {max_cloud_cover}"
        
        odata_filter = f"{date_filter} and {bbox_filter} and {platform_filter} and {product_filter} and {cloud_filter}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/resto/api/collections/Sentinel2/search.json",
                params={
                    "$filter": odata_filter,
                    "$top": limit,
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            results = response.json()
            
            scenes = []
            for feature in results.get("features", []):
                props = feature.get("properties", {})
                scenes.append({
                    "id": feature.get("id", ""),
                    "platform": "Sentinel-2",
                    "acquisition_date": props.get("completionTime", ""),
                    "cloud_cover": props.get("cloudCover", 0),
                    "product_type": product_level,
                    "url": self._get_download_url(feature),
                    "bounds": self._extract_bounds(feature),
                })
            
            return scenes
    
    def _get_download_url(self, feature: Dict) -> str:
        """Extract download URL from feature"""
        links = feature.get("links", [])
        for link in links:
            if link.get("rel") == "self":
                href = link.get("href", "")
                # Convert to download URL
                if "download" not in href:
                    return href.replace("/products/", "/odata/v1/Products(") + "/$value"
                return href
        return ""
    
    def _extract_bounds(self, feature: Dict) -> Dict[str, float]:
        """Extract bounding box from feature geometry"""
        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates", [[]])[0]
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        return {
            "minLat": min(lats),
            "maxLat": max(lats),
            "minLng": min(lons),
            "maxLng": max(lons),
        }
    
    async def download_scene(self, scene_url: str, output_path: str) -> str:
        """Download a satellite scene to local storage"""
        token = await self._get_token()
        
        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
            async with client.stream(
                "GET",
                scene_url,
                headers={"Authorization": f"Bearer {token}"},
            ) as response:
                response.raise_for_status()
                
                with open(output_path, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
        
        return output_path


# Singleton instance
copernicus_client = CopernicusClient()
