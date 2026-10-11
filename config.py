"""
Configuration module for the SurplusLink Hyperlocal Lead Generation Engine.
Loads settings from environment variables or .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def is_placeholder(val: str) -> bool:
    """Check if the config value is a placeholder string."""
    if not val:
        return True
    val_clean = val.strip().lower().strip("[]'\"")
    return (
        "your" in val_clean
        or "token" in val_clean
        or "publishable key" in val_clean
        or val_clean in ["none", "null", "", "..."]
    )


class Config:
    """SurplusLink Lead Generation Engine Settings."""

    # Supabase credentials (auto-strip bracket wrappers if pasted by user)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "").strip().strip("[]'\"")
    SUPABASE_KEY: str = (
        os.getenv("SUPABASE_KEY", "")
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        or os.getenv("SUPABASE_ANON_KEY", "")
    ).strip().strip("[]'\"")

    # SerpApi credentials (supports SERPAPI_KEY or SERPAPI_API_KEY)
    SERPAPI_API_KEY: str = (
        os.getenv("SERPAPI_KEY", "")
        or os.getenv("SERPAPI_API_KEY", "")
    ).strip().strip("[]'\"")

    # Lead generation parameters
    SEARCH_RADIUS_KM: float = float(os.getenv("SEARCH_RADIUS_KM", "5.0"))
    MAX_LEADS_PER_LISTING: int = int(os.getenv("MAX_LEADS_PER_LISTING", "3"))
    POLL_INTERVAL_SECONDS: int = int(os.getenv("POLL_INTERVAL_SECONDS", "5"))

    # Mock mode fallback when keys are placeholders
    MOCK_MODE_IF_UNCONFIGURED: bool = os.getenv(
        "MOCK_MODE_IF_UNCONFIGURED", "true"
    ).lower() in ("true", "1", "yes")

    @classmethod
    def is_supabase_configured(cls) -> bool:
        """Check if real Supabase credentials are provided."""
        return not is_placeholder(cls.SUPABASE_URL) and not is_placeholder(cls.SUPABASE_KEY)

    @classmethod
    def is_serpapi_configured(cls) -> bool:
        """Check if real SerpApi credentials are provided."""
        return not is_placeholder(cls.SERPAPI_API_KEY)

    @classmethod
    def is_live_configured(cls) -> bool:
        """Check if both Supabase and SerpApi are fully configured."""
        return cls.is_supabase_configured() and cls.is_serpapi_configured()

    @classmethod
    def summary(cls) -> str:
        """Return human-readable summary of config state."""
        sb_status = "Configured (Live)" if cls.is_supabase_configured() else "Placeholder / Not configured"
        serp_status = "Configured (Live)" if cls.is_serpapi_configured() else "Placeholder / Not configured"
        mode = "Live Database & Live SerpApi" if cls.is_live_configured() else (
            "Simulation / Dry-Run (Mock Mode enabled)" if cls.MOCK_MODE_IF_UNCONFIGURED else "Incomplete Credentials"
        )
        return (
            f"Configuration Status:\n"
            f"  - Supabase URL: {'Set' if cls.is_supabase_configured() else cls.SUPABASE_URL or 'Missing'} ({sb_status})\n"
            f"  - Supabase Key: {'Set' if cls.is_supabase_configured() else cls.SUPABASE_KEY or 'Missing'}\n"
            f"  - SerpApi Key:  {'Set' if cls.is_serpapi_configured() else cls.SERPAPI_API_KEY or 'Missing'} ({serp_status})\n"
            f"  - Search Radius: {cls.SEARCH_RADIUS_KM} km\n"
            f"  - Max Leads per Listing: {cls.MAX_LEADS_PER_LISTING}\n"
            f"  - Polling Interval: {cls.POLL_INTERVAL_SECONDS}s\n"
            f"  - Active Mode: {mode}"
        )
