"""
ERCOT Real-Time Price Ingestion Job
Runs every 5 minutes to fetch latest Settlement Point Prices
"""
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.backend.ercot.ingestion import ERCOTIngestionService


async def main():
    """Main ingestion job"""
    print(f"[{datetime.now()}] Starting ERCOT real-time price ingestion...")

    # Get API key from environment (optional for public data)
    api_key = os.environ.get('ERCOT_API_KEY')

    service = ERCOTIngestionService(api_key)

    # Key settlement points to monitor
    settlement_points = [
        'HB_BUSAVG',      # System average
        'HB_HOUSTON',     # Houston hub
        'HB_NORTH',       # North hub
        'HB_SOUTH',       # South hub
        'HB_WEST',        # West hub
    ]

    try:
        total_records = 0

        for settlement_point in settlement_points:
            print(f"\n[{datetime.now()}] Ingesting {settlement_point}...")

            # Fetch last 1 hour of 5-minute prices
            result = await service.ingest_real_time_prices(
                settlement_point=settlement_point,
                lookback_hours=1
            )

            print(f"  Status: {result['status']}")
            print(f"  Records loaded: {result.get('records_loaded', 0)}")
            print(f"  Interval: {result.get('interval')}")

            total_records += result.get('records_loaded', 0)

        print(f"\n[{datetime.now()}] Total records loaded: {total_records}")

    except Exception as e:
        print(f"[{datetime.now()}] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        await service.close()

    print(f"[{datetime.now()}] ERCOT ingestion job completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
