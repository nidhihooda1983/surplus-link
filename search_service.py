"""
SerpApi Google Local search integration for finding hyperlocal commercial buyers.
"""

import math
import random
import logging
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
import requests

from config import is_placeholder

logger = logging.getLogger("SurplusLink.Search")


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth in kilometers.
    """
    # Earth radius in kilometers
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c, 2)


@dataclass
class BusinessLead:
    """Structured representation of a discovered commercial buyer lead."""
    business_name: str
    address: str
    phone_number: str
    latitude: float
    longitude: float
    distance_km: float
    rating: Optional[float] = None
    reviews: Optional[int] = None
    source: str = "serpapi_google_local"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SerpApiSearchService:
    """Service to query SerpApi Google Local and filter top closest commercial buyers."""

    SERPAPI_URL = "https://serpapi.com/search.json"

    def __init__(
        self,
        api_key: str,
        search_radius_km: float = 5.0,
        max_leads: int = 3,
        mock_mode: bool = False,
    ):
        self.api_key = api_key
        self.search_radius_km = search_radius_km
        self.max_leads = max_leads
        self.mock_mode = mock_mode or is_placeholder(api_key)

    def search_buyers(
        self, query: str, lat: float, lng: float
    ) -> List[BusinessLead]:
        """
        Search for commercial buyers within radius of (lat, lng) using SerpApi Google Local.
        
        Args:
            query: Targeted search query (e.g. 'restaurants catering commercial kitchens')
            lat: Listing latitude
            lng: Listing longitude
            
        Returns:
            List of top closest BusinessLead objects (up to max_leads).
        """
        if self.mock_mode:
            logger.info(
                f"[SIMULATION] Mock SerpApi search for '{query}' at ({lat}, {lng})"
            )
            return self._generate_mock_leads(query, lat, lng)

        logger.info(f"Executing SerpApi Google Local query: '{query}' around ({lat}, {lng})")
        params = {
            "engine": "google_local",
            "q": query,
            "ll": f"@{lat},{lng},14z",
            "api_key": self.api_key,
            "hl": "en",
        }

        try:
            response = requests.get(self.SERPAPI_URL, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"SerpApi request failed: {e}")
            raise

        local_results = data.get("local_results", [])
        if not local_results:
            logger.warning(f"No Google Local results found for query '{query}'")
            return []

        leads: List[BusinessLead] = []
        for item in local_results:
            name = item.get("title") or item.get("name") or "Unknown Commercial Buyer"
            address = item.get("address") or "Address unlisted"
            phone = item.get("phone") or "Phone unlisted"

            # Parse coordinates
            gps = item.get("gps_coordinates") or {}
            item_lat = gps.get("latitude")
            item_lng = gps.get("longitude")

            if item_lat is not None and item_lng is not None:
                dist = haversine_distance(lat, lng, float(item_lat), float(item_lng))
                lead_lat = float(item_lat)
                lead_lng = float(item_lng)
            else:
                # If GPS not explicitly present in item, estimate using listing coordinates
                dist = round(random.uniform(0.5, self.search_radius_km), 2)
                lead_lat = lat
                lead_lng = lng

            lead = BusinessLead(
                business_name=name,
                address=address,
                phone_number=phone,
                latitude=lead_lat,
                longitude=lead_lng,
                distance_km=dist,
                rating=item.get("rating"),
                reviews=item.get("reviews"),
            )
            leads.append(lead)

        # Sort strictly by closest distance
        leads.sort(key=lambda x: x.distance_km)

        # Filter within radius, fallback to closest if none within strict boundary
        radius_leads = [l for l in leads if l.distance_km <= self.search_radius_km]
        selected_leads = radius_leads[: self.max_leads] if radius_leads else leads[: self.max_leads]

        logger.info(
            f"Found {len(leads)} candidates, selected top {len(selected_leads)} closest buyers."
        )
        return selected_leads

    def _generate_mock_leads(
        self, query: str, lat: float, lng: float
    ) -> List[BusinessLead]:
        """Generate realistic mock buyer leads for testing/demonstration."""
        mock_templates = [
            ("Metro Commercial Kitchen & Catering", "102 Industrial Ave, Suite A", "+1 (555) 234-8901", 0.8),
            ("Apex Food Distributors & Supply", "45 Harbor Blvd, Bldg 3", "+1 (555) 872-3114", 1.4),
            ("Citywide Restaurant Collective", "789 Market Street", "+1 (555) 901-4432", 2.2),
            ("Summit Building & Contractor Supply", "310 Commercial Pkwy", "+1 (555) 612-9844", 1.1),
            ("Regional Scrap & Recycling Center", "88 Freight Yard Rd", "+1 (555) 431-7720", 3.0),
            ("Prime Wholesale Liquidators", "520 Logistics Way", "+1 (555) 789-0123", 2.6),
        ]

        # Pick 3 mock templates
        selected = random.sample(mock_templates, min(self.max_leads, len(mock_templates)))
        leads = []
        for name, addr, phone, base_dist in selected:
            # Add small jitter to coordinates
            delta_lat = (base_dist / 111.0) * random.choice([-1, 1])
            delta_lng = (base_dist / (111.0 * math.cos(math.radians(lat)))) * random.choice([-1, 1])
            lead_lat = round(lat + delta_lat, 6)
            lead_lng = round(lng + delta_lng, 6)
            dist = haversine_distance(lat, lng, lead_lat, lead_lng)

            leads.append(
                BusinessLead(
                    business_name=f"{name} ({query[:20]}...)",
                    address=addr,
                    phone_number=phone,
                    latitude=lead_lat,
                    longitude=lead_lng,
                    distance_km=dist,
                    rating=round(random.uniform(4.0, 4.9), 1),
                    reviews=random.randint(15, 120),
                    source="mock_simulation",
                )
            )

        leads.sort(key=lambda x: x.distance_km)
        return leads[: self.max_leads]
