"""
Core orchestrator for the SurplusLink Hyperlocal Lead Generation Engine.
Executes the continuous monitoring and lead discovery workflow loop.
"""

import time
import logging
from typing import Set, Dict, Any, List, Optional

from config import Config
from query_formulator import QueryFormulator
from search_service import SerpApiSearchService, BusinessLead
from db_service import DatabaseService

logger = logging.getLogger("SurplusLink.Engine")


class LeadGenerationEngine:
    """
    Hyperlocal Lead Generation Engine for SurplusLink B2B platform.
    
    Workflow Loop:
    1. Monitor Supabase 'listings' table for rows where status = 'Available'.
    2. Extract 'item_name', 'category', 'location_lat', 'location_lng'.
    3. Formulate targeted SerpApi Google Local query for immediate commercial buyers.
    4. Execute SerpApi search and retrieve top 3 closest business results.
    5. Write discovered buyers to 'scraped_leads' table linked via 'listing_id' with lead_status = 'Discovered'.
    """

    def __init__(
        self,
        db_service: Optional[DatabaseService] = None,
        search_service: Optional[SerpApiSearchService] = None,
        search_radius_km: float = Config.SEARCH_RADIUS_KM,
        max_leads: int = Config.MAX_LEADS_PER_LISTING,
        poll_interval: int = Config.POLL_INTERVAL_SECONDS,
    ):
        self.db = db_service or DatabaseService()
        self.search = search_service or SerpApiSearchService(
            api_key=Config.SERPAPI_API_KEY,
            search_radius_km=search_radius_km,
            max_leads=max_leads,
        )
        self.search_radius_km = search_radius_km
        self.max_leads = max_leads
        self.poll_interval = poll_interval
        self.processed_listing_ids: Set[str] = set()

    def process_listing(self, listing: Dict[str, Any]) -> List[BusinessLead]:
        """
        Process a single available listing through steps 2-5 of the workflow loop.
        """
        listing_id = str(listing.get("id"))
        item_name = listing.get("item_name") or "Unspecified Item"
        category = listing.get("category") or "General"
        
        # Extract coordinates
        try:
            lat = float(listing.get("location_lat"))
            lng = float(listing.get("location_lng"))
        except (TypeError, ValueError) as err:
            logger.error(
                f"Listing {listing_id} has invalid coordinates (lat={listing.get('location_lat')}, lng={listing.get('location_lng')}): {err}"
            )
            self.processed_listing_ids.add(listing_id)
            return []

        logger.info("=" * 70)
        logger.info(f"⚡ [NEW LISTING DETECTED] ID: {listing_id}")
        logger.info(f"   Item:       {item_name}")
        logger.info(f"   Category:   {category}")
        logger.info(f"   Location:   ({lat}, {lng})")

        # Check if leads were already generated previously (idempotence)
        existing_count = self.db.get_existing_leads_count(listing_id)
        if existing_count > 0:
            logger.info(
                f"Listing {listing_id} already has {existing_count} leads in 'scraped_leads'. Skipping."
            )
            self.processed_listing_ids.add(listing_id)
            return []

        # Step 3: Formulate targeted SerpApi Google Local query
        query = QueryFormulator.formulate_query(item_name=item_name, category=category)
        logger.info(f"🎯 [QUERY FORMULATED] Target: '{query}' (Radius: {self.search_radius_km}km)")

        # Step 4: Execute SerpApi Google Local query & collect top 3 closest buyers
        try:
            buyers = self.search.search_buyers(query=query, lat=lat, lng=lng)
        except Exception as err:
            logger.error(f"Failed to execute SerpApi search for listing {listing_id}: {err}")
            return []

        if not buyers:
            logger.warning(f"No commercial buyers found within radius for listing {listing_id}")
            self.processed_listing_ids.add(listing_id)
            return []

        # Step 5: Write rows into 'scraped_leads' table
        logger.info(f"📥 [STORING LEADS] Writing {len(buyers)} buyers into 'scraped_leads'...")
        for rank, buyer in enumerate(buyers, 1):
            logger.info(
                f"   #{rank}: {buyer.business_name} | Dist: {buyer.distance_km}km | "
                f"Phone: {buyer.phone_number} | Addr: {buyer.address}"
            )
            try:
                self.db.insert_lead(listing_id=listing_id, lead=buyer, query_used=query)
            except Exception as e:
                logger.error(f"Error inserting lead '{buyer.business_name}': {e}")

        # Mark as processed in local cache
        self.processed_listing_ids.add(listing_id)
        logger.info(f"✅ Successfully processed listing {listing_id} -> {len(buyers)} leads stored.")
        return buyers

    def run_iteration(self) -> int:
        """
        Execute one poll iteration of Step 1:
        Monitor Supabase 'listings' table where status = 'Available'.
        Returns total number of new leads generated in this iteration.
        """
        listings = self.db.fetch_available_listings()
        new_listings = [
            l for l in listings if str(l.get("id")) not in self.processed_listing_ids
        ]

        if not new_listings:
            logger.debug("No new 'Available' listings found in this iteration.")
            return 0

        logger.info(f"Found {len(new_listings)} pending 'Available' listing(s) to process.")
        total_leads = 0
        for listing in new_listings:
            leads = self.process_listing(listing)
            total_leads += len(leads)

        return total_leads

    def run_loop(self, interval_seconds: Optional[int] = None) -> None:
        """
        Continuously execute the workflow monitoring loop.
        """
        interval = interval_seconds or self.poll_interval
        logger.info("=" * 70)
        logger.info("🚀 SURPLUSLINK HYPERLOCAL LEAD GENERATION ENGINE STARTED")
        logger.info(f"   Polling Interval: {interval} seconds")
        logger.info(f"   Search Radius:    {self.search_radius_km} km")
        logger.info(f"   Max Leads/Item:   {self.max_leads}")
        logger.info("   Press Ctrl+C to stop the engine.")
        logger.info("=" * 70)

        iteration = 1
        try:
            while True:
                logger.debug(f"--- Iteration #{iteration} checking for 'Available' listings ---")
                try:
                    self.run_iteration()
                except Exception as loop_err:
                    logger.error(f"Unexpected error in iteration #{iteration}: {loop_err}", exc_info=True)

                iteration += 1
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Engine shutdown signal received. Stopping gracefully...")
