#!/usr/bin/env python3
"""
Quick test script to verify ERCOT API connectivity
Run: python test_ercot_api.py
"""
import asyncio
from datetime import datetime, timedelta
from app.backend.config import get_settings
from app.backend.ercot.client import ERCOTClient
from app.backend.ercot.ingestion import get_ercot_ingestion_service


async def test_ercot_connection():
    """Test ERCOT API connection with configured keys"""
    print("=" * 60)
    print("ERCOT API Connection Test")
    print("=" * 60)

    # Test 1: Check configuration
    settings = get_settings()
    api_key = settings.ercot_api_key

    if api_key:
        print(f"✅ API Key configured: {api_key[:8]}...{api_key[-8:]}")
    else:
        print("❌ No API key found in configuration")
        return

    print()

    # Test 2: Test client initialization
    print("Test 1: Client Initialization")
    print("-" * 60)
    try:
        client = ERCOTClient(api_key=api_key)
        print("✅ ERCOT Client initialized successfully")
        print(f"   Base URL: {client.BASE_URL}")
        print(f"   Timeout: {client.timeout}s")
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        return

    print()

    # Test 3: Test real-time price fetching
    print("Test 2: Fetch Real-Time Prices (Last 1 hour)")
    print("-" * 60)
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)

        print(f"   Settlement Point: HB_BUSAVG (System Average)")
        print(f"   Time Range: {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}")

        prices = await client.get_real_time_prices(
            settlement_point='HB_BUSAVG',
            start_datetime=start_time,
            end_datetime=end_time
        )

        if prices:
            print(f"✅ Fetched {len(prices)} price records")
            print(f"   Expected: ~12 records (5-min intervals)")

            # Show latest price
            if prices:
                latest = prices[0]
                print(f"\n   Latest Price:")
                print(f"   - Timestamp: {latest['interval_datetime']}")
                print(f"   - SPP: ${latest['spp_usd_mwh']:.2f}/MWh")
                print(f"   - Congestion: ${latest['congestion_price_usd_mwh']:.2f}/MWh")
                print(f"   - Loss: ${latest['loss_price_usd_mwh']:.2f}/MWh")
        else:
            print("⚠️  No prices returned (may be normal if outside trading hours)")

    except Exception as e:
        print(f"❌ Price fetch failed: {e}")
        print(f"   Error type: {type(e).__name__}")

    print()

    # Test 4: Test ingestion service
    print("Test 3: Ingestion Service")
    print("-" * 60)
    try:
        service = get_ercot_ingestion_service()
        print("✅ Ingestion service initialized")
        print(f"   Catalog: {service.catalog}")

        # Note: Don't actually run ingestion in test, just verify setup
        print("   (Skipping actual ingestion - run manually when ready)")

    except Exception as e:
        print(f"❌ Ingestion service failed: {e}")

    print()

    # Test 5: Test available endpoints
    print("Test 4: Available ERCOT Data Sources")
    print("-" * 60)
    print("✅ Settlement Points Available:")
    for code, name in ERCOTClient.SETTLEMENT_POINTS.items():
        print(f"   - {code}: {name}")

    print()
    print("=" * 60)
    print("ERCOT API Test Complete!")
    print("=" * 60)
    print()
    print("Next Steps:")
    print("1. If all tests passed, your ERCOT integration is ready")
    print("2. Run schema migration: data/schema/09_multi_market_expansion.sql")
    print("3. Deploy Databricks jobs: databricks/jobs/ercot_*.yaml")
    print("4. Start ingestion via API: POST /api/v1/ercot/ingest/real-time-prices")
    print()

    await client.close()


if __name__ == "__main__":
    asyncio.run(test_ercot_connection())
