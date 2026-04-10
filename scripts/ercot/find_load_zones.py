#!/usr/bin/env python3
"""
Find load zone settlement points in ERCOT CSV
"""
import asyncio
import httpx
import zipfile
import io
import csv as csv_module

async def find_load_zones():
    """Find load zone names in ERCOT CSV"""

    async with httpx.AsyncClient(timeout=30) as client:
        # Get SPP document list
        response = await client.get(
            "https://www.ercot.com/misapp/servlets/IceDocListJsonWS",
            params={"reportTypeId": "12301"}  # SPP RT
        )

        data = response.json()
        docs = data.get('ListDocsByRptTypeRes', {}).get('DocumentList', [])

        # Get latest CSV document
        for doc_entry in docs[:1]:
            doc = doc_entry.get('Document', {})
            friendly_name = doc.get('FriendlyName', '')

            if friendly_name.endswith('_csv'):
                doc_id = doc.get('DocID')
                print(f"Analyzing: {friendly_name}")
                print("=" * 70)

                # Download and extract
                download_response = await client.get(
                    "https://www.ercot.com/misdownload/servlets/mirDownload",
                    params={"doclookupId": doc_id}
                )

                zip_data = download_response.content

                with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                    csv_filename = next((f for f in zf.namelist() if f.endswith('.csv')), None)

                    if csv_filename:
                        csv_bytes = zf.read(csv_filename)
                        content = csv_bytes.decode('utf-8')

                        # Find all load zones
                        reader = csv_module.DictReader(io.StringIO(content))

                        lz_points = {}
                        hub_points = {}

                        for row in reader:
                            name = row.get('SettlementPointName', '')
                            point_type = row.get('SettlementPointType', '')
                            price = row.get('SettlementPointPrice', '0')

                            # Look for load zones
                            if name.startswith('LZ_'):
                                lz_points[name] = {
                                    'type': point_type,
                                    'price': price
                                }

                            # Look for hubs
                            if name.startswith('HB_'):
                                hub_points[name] = {
                                    'type': point_type,
                                    'price': price
                                }

                        print()
                        print("LOAD ZONES Found:")
                        print("-" * 70)
                        for name, info in sorted(lz_points.items()):
                            print(f"  {name:30} Type: {info['type']:10} Price: ${info['price']}/MWh")

                        print()
                        print("HUBS Found:")
                        print("-" * 70)
                        for name, info in sorted(hub_points.items()):
                            print(f"  {name:30} Type: {info['type']:10} Price: ${info['price']}/MWh")

                        print()
                        print(f"Total Load Zones: {len(lz_points)}")
                        print(f"Total Hubs: {len(hub_points)}")

                break

if __name__ == "__main__":
    asyncio.run(find_load_zones())
