"""
NEMWEB Real-Time Data Ingestion Job
Runs every 5 minutes to fetch latest dispatch prices from NEMWEB
"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.backend.nemweb.ingestion import NEMWEBIngestionService


async def main():
    """Main ingestion job"""
    print(f"[{datetime.now()}] Starting NEMWEB real-time ingestion...")

    service = NEMWEBIngestionService()

    try:
        # Ingest dispatch prices for today
        result = await service.ingest_dispatch_prices()

        print(f"[{datetime.now()}] Ingestion completed:")
        print(f"  Status: {result['status']}")
        print(f"  Records loaded: {result.get('records_loaded', 0)}")

        if result['status'] == 'FAILED':
            print(f"  Error: {result.get('error_message')}")
            sys.exit(1)

    except Exception as e:
        print(f"[{datetime.now()}] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        if service.client:
            await service.client.close()

    print(f"[{datetime.now()}] NEMWEB ingestion job completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
