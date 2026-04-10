#!/usr/bin/env python3
"""
Direct ERCOT API test with various authentication methods
"""
import asyncio
import os
import httpx

API_KEY = os.getenv("ERCOT_API_KEY", "")

async def test_ercot_endpoints():
    """Test different ERCOT API endpoints and auth methods"""

    async with httpx.AsyncClient(timeout=30) as client:
        print("=" * 70)
        print("ERCOT API Direct Test - Testing Authentication Methods")
        print("=" * 70)
        print()

        if API_KEY:
            print("Using ERCOT API key from ERCOT_API_KEY environment variable")
        else:
            print("No ERCOT_API_KEY set; authenticated endpoint tests may return 401/403")
        print()

        # Test 1: Try with Ocp-Apim-Subscription-Key header
        print("Test 1: Ocp-Apim-Subscription-Key header")
        print("-" * 70)
        try:
            response = await client.get(
                "https://www.ercot.com/api/1/services/read/dashboards/todays-outlook",
                headers={"Ocp-Apim-Subscription-Key": API_KEY}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ SUCCESS! Data retrieved:")
                print(response.text[:500])
            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"Response: {response.text[:200]}")
        except Exception as e:
            print(f"❌ Error: {e}")

        print()

        # Test 2: Try without any auth (public endpoints)
        print("Test 2: Public endpoint (no auth)")
        print("-" * 70)
        try:
            response = await client.get(
                "https://www.ercot.com/api/1/services/read/dashboards/todays-outlook"
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ SUCCESS! Public data available:")
                data = response.json()
                print(f"Data type: {type(data)}")
                if isinstance(data, dict):
                    print(f"Keys: {list(data.keys())[:5]}")
                elif isinstance(data, list):
                    print(f"Records: {len(data)}")
            else:
                print(f"❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")

        print()

        # Test 3: Check API documentation endpoint
        print("Test 3: API Info/Documentation endpoint")
        print("-" * 70)
        try:
            response = await client.get(
                "https://www.ercot.com/api/1/",
                headers={"Ocp-Apim-Subscription-Key": API_KEY}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:300]}")
        except Exception as e:
            print(f"Error: {e}")

        print()

        # Test 4: Try alternative base URLs
        print("Test 4: Alternative ERCOT Data Sources")
        print("-" * 70)

        # ERCOT Mis-Reports (public data)
        try:
            response = await client.get(
                "https://www.ercot.com/misapp/servlets/IceDocListJsonWS?reportTypeId=13101"
            )
            print(f"Mis-Reports endpoint: {response.status_code}")
            if response.status_code == 200:
                print("✅ Public data portal accessible")
        except Exception as e:
            print(f"Mis-Reports error: {e}")

        print()
        print("=" * 70)
        print("ANALYSIS")
        print("=" * 70)
        print()
        print("The 403 Forbidden error suggests:")
        print("1. API keys may need to be approved/activated by ERCOT")
        print("2. Your subscription might be pending activation")
        print("3. Specific endpoints might require different subscription tiers")
        print("4. IP whitelisting might be required")
        print()
        print("Recommendations:")
        print("1. Check ERCOT developer portal: https://developer.ercot.com/")
        print("2. Verify API key status in your ERCOT account")
        print("3. Review any activation emails from ERCOT")
        print("4. Contact ERCOT API support if keys were just created")
        print()
        print("Alternative: Use ERCOT public data portals:")
        print("- Mis-Reports: https://www.ercot.com/misapp/servlets/IceDocListJsonWS")
        print("- Public datasets available without authentication")
        print()

if __name__ == "__main__":
    asyncio.run(test_ercot_endpoints())
