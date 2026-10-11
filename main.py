"""
CLI Entrypoint for the SurplusLink Hyperlocal Lead Generation Engine.
"""

import argparse
import sys
import logging

from config import Config
from engine import LeadGenerationEngine
from db_service import DatabaseService


def setup_logging(verbose: bool = False):
    """Configure structured logging output."""
    level = logging.DEBUG if verbose else logging.INFO
    format_str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(level=level, format=format_str, datefmt="%Y-%m-%d %H:%M:%S")


def main():
    parser = argparse.ArgumentParser(
        description="SurplusLink Hyperlocal Lead Generation Engine"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single poll iteration and exit (ideal for cron or test)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=Config.POLL_INTERVAL_SECONDS,
        help="Seconds between Supabase polling iterations",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable detailed debug logging",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print current environment and configuration status",
    )
    parser.add_argument(
        "--seed-test",
        action="store_true",
        help="Insert a sample 'Available' listing for testing",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Force mock/simulation mode even if credentials are set",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    if args.status:
        print(Config.summary())
        return

    # Print startup configuration summary
    print(Config.summary())
    print()

    db = DatabaseService(mock_mode=args.mock)
    engine = LeadGenerationEngine(db_service=db, poll_interval=args.interval)

    if args.seed_test:
        db.insert_test_listing(
            item_name="Surplus 200 Fresh Bakery Sourdough Loaves",
            category="Food & Bakery",
            lat=37.7749,
            lng=-122.4194,
            quantity=200,
            unit="loaves",
        )

    if args.once:
        print("Running single iteration...")
        leads_count = engine.run_iteration()
        print(f"Single iteration complete. Total leads generated: {leads_count}")
        sys.exit(0)

    # Run continuous monitoring loop
    engine.run_loop()


if __name__ == "__main__":
    main()
