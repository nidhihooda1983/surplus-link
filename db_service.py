"""
Database service for Supabase integration.
Monitors the 'listings' table and writes generated leads to the 'scraped_leads' table.
"""

import uuid
import logging
from typing import List, Dict, Any, Optional
from dataclasses import asdict

from config import Config, is_placeholder
from search_service import BusinessLead

logger = logging.getLogger("SurplusLink.DB")


class MockSupabaseClient:
    """In-memory mock database for testing and demonstration without live credentials."""

    def __init__(self):
        self.listings: List[Dict[str, Any]] = []
        self.scraped_leads: List[Dict[str, Any]] = []
        self._seed_default_listings()

    def _seed_default_listings(self):
        """Seed initial test listings with status = 'Available'."""
        self.listings = [
            {
                "id": str(uuid.uuid4()),
                "item_name": "500kg Fresh Organic Tomatoes",
                "category": "Food & Agriculture",
                "location_lat": 37.7749,
                "location_lng": -122.4194,
                "status": "Available",
                "quantity": 500,
                "unit": "kg",
            },
            {
                "id": str(uuid.uuid4()),
                "item_name": "Surplus Red Clay Construction Bricks (2,000 units)",
                "category": "Construction Materials",
                "location_lat": 37.7833,
                "location_lng": -122.4167,
                "status": "Available",
                "quantity": 2000,
                "unit": "units",
            },
            {
                "id": str(uuid.uuid4()),
                "item_name": "Industrial Copper Wire & Cable Scrap (150kg)",
                "category": "Scrap & Recycling",
                "location_lat": 37.7651,
                "location_lng": -122.4241,
                "status": "Available",
                "quantity": 150,
                "unit": "kg",
            },
        ]


class DatabaseService:
    """Interface to Supabase for reading listings and writing discovered leads."""

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        mock_mode: bool = False,
    ):
        self.url = supabase_url or Config.SUPABASE_URL
        self.key = supabase_key or Config.SUPABASE_KEY
        self.mock_mode = (
            mock_mode
            or is_placeholder(self.url)
            or is_placeholder(self.key)
        )
        self.client = None
        self.mock_db: Optional[MockSupabaseClient] = None

        if self.mock_mode:
            logger.info("Initializing DatabaseService in SIMULATED / MOCK mode.")
            self.mock_db = MockSupabaseClient()
        else:
            try:
                from supabase import create_client, Client
                logger.info(f"Connecting to live Supabase at {self.url}...")
                self.client: Client = create_client(self.url, self.key)
                logger.info("Connected to Supabase successfully.")
            except Exception as e:
                logger.error(f"Failed to connect to Supabase: {e}")
                if Config.MOCK_MODE_IF_UNCONFIGURED:
                    logger.warning("Falling back to Simulated Mock Database.")
                    self.mock_mode = True
                    self.mock_db = MockSupabaseClient()
                else:
                    raise

    def fetch_available_listings(self) -> List[Dict[str, Any]]:
        """
        Fetch all listings where status = 'Available'.
        """
        if self.mock_mode:
            available = [
                row for row in self.mock_db.listings if row.get("status") == "Available"
            ]
            return available

        try:
            response = (
                self.client.table("listings")
                .select("*")
                .eq("status", "Available")
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Error querying Supabase listings table: {e}")
            return []

    def get_existing_leads_count(self, listing_id: str) -> int:
        """Check how many leads have already been recorded for a listing."""
        if self.mock_mode:
            return sum(
                1 for lead in self.mock_db.scraped_leads if lead.get("listing_id") == str(listing_id)
            )

        try:
            response = (
                self.client.table("scraped_leads")
                .select("id", count="exact")
                .eq("listing_id", listing_id)
                .execute()
            )
            return response.count or len(response.data or [])
        except Exception as e:
            logger.warning(f"Could not check existing leads for listing {listing_id}: {e}")
            return 0

    def insert_lead(
        self,
        listing_id: str,
        lead: BusinessLead,
        query_used: str = "",
    ) -> Dict[str, Any]:
        """
        Insert a discovered buyer into the 'scraped_leads' table.
        Linked via 'listing_id', setting 'lead_status' to 'Discovered'.
        """
        # Primary payload matching live Supabase scraped_leads table schema
        payload = {
            "listing_id": str(listing_id),
            "business_name": lead.business_name,
            "phone_number": lead.phone_number,
            "distance_km": lead.distance_km,
            "location_lat": lead.latitude,
            "location_lng": lead.longitude,
            "lead_status": "Discovered",
        }

        # Extended metadata fields (if supported by database schema)
        extended_payload = {
            **payload,
            "address": lead.address,
            "latitude": lead.latitude,
            "longitude": lead.longitude,
            "query_used": query_used,
        }

        if self.mock_mode:
            mock_row = {
                "id": str(uuid.uuid4()),
                **extended_payload,
            }
            self.mock_db.scraped_leads.append(mock_row)
            logger.info(
                f"[SIMULATION] Saved lead to 'scraped_leads': {lead.business_name} (listing_id={listing_id})"
            )
            return mock_row

        try:
            # Try inserting extended payload first
            response = self.client.table("scraped_leads").insert(extended_payload).execute()
            logger.info(
                f"Saved lead to Supabase 'scraped_leads': {lead.business_name} (listing_id={listing_id})"
            )
            return response.data[0] if response.data else payload
        except Exception as e:
            # If extra column fails (e.g. strict minimal schema), retry with minimal payload
            logger.warning(
                f"Extended insert failed ({e}), retrying with minimal required columns..."
            )
            try:
                response = self.client.table("scraped_leads").insert(payload).execute()
                logger.info(
                    f"Saved minimal lead to Supabase 'scraped_leads': {lead.business_name}"
                )
                return response.data[0] if response.data else payload
            except Exception as e2:
                logger.error(f"Failed to insert lead into Supabase: {e2}")
                raise e2

    def update_listing_status(self, listing_id: str, new_status: str) -> None:
        """Update status of a listing (e.g. to 'Processing' or 'Leads_Discovered')."""
        if self.mock_mode:
            for item in self.mock_db.listings:
                if str(item.get("id")) == str(listing_id):
                    item["status"] = new_status
            logger.debug(f"[SIMULATION] Updated listing {listing_id} status to '{new_status}'")
            return

        try:
            self.client.table("listings").update({"status": new_status}).eq("id", listing_id).execute()
            logger.debug(f"Updated listing {listing_id} status to '{new_status}'")
        except Exception as e:
            logger.warning(f"Failed to update listing status: {e}")

    def insert_test_listing(
        self,
        item_name: str,
        category: str,
        lat: float,
        lng: float,
        quantity: float = 100,
        unit: str = "units",
    ) -> Dict[str, Any]:
        """Convenience method to insert a test listing for testing the loop."""
        new_listing = {
            "id": str(uuid.uuid4()),
            "item_name": item_name,
            "category": category,
            "location_lat": lat,
            "location_lng": lng,
            "status": "Available",
            "quantity": quantity,
            "unit": unit,
        }

        if self.mock_mode:
            self.mock_db.listings.append(new_listing)
            logger.info(f"[SIMULATION] Added test listing: {item_name}")
            return new_listing

        try:
            res = self.client.table("listings").insert(new_listing).execute()
            logger.info(f"Added test listing to Supabase: {item_name}")
            return res.data[0] if res.data else new_listing
        except Exception as e:
            logger.error(f"Failed to insert test listing into Supabase: {e}")
            raise
