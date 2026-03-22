"""
EPEX Day-Ahead Price Ingestion Job
Runs daily to fetch day-ahead auction prices from ENTSOE
"""
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.backend.epex.ingestion import EPEXIngestionService


async def main():
    """Main ingestion job"""
    print(f"[{datetime.now()}] Starting EPEX day-ahead price ingestion...")

    # Get API key from environment
    api_key = os.environ.get('ENTSOE_API_KEY')
    if not api_key:
        print("ERROR: ENTSOE_API_KEY environment variable not set")
        sys.exit(1)

    service = EPEXIngestionService(api_key)

    # Market areas to ingest
    market_areas = ['DE', 'FR', 'NL', 'BE', 'AT']

    try:
        total_records = 0

        for market_area in market_areas:
            print(f"\n[{datetime.now()}] Ingesting {market_area}...")

            result = await service.ingest_day_ahead_prices(market_area)

            print(f"  Status: {result['status']}")
            print(f"  Records loaded: {result.get('records_loaded', 0)}")

            total_records += result.get('records_loaded', 0)

        print(f"\n[{datetime.now()}] Total records loaded: {total_records}")

    except Exception as e:
        print(f"[{datetime.now()}] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        await service.close()

    print(f"[{datetime.now()}] EPEX ingestion job completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
