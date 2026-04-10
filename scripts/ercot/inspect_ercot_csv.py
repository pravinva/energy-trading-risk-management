#!/usr/bin/env python3
"""
Inspect ERCOT CSV format to understand column names
"""
import asyncio
import httpx
import zipfile
import io

async def inspect_ercot_csv():
    """Download and inspect actual ERCOT CSV format"""

    async with httpx.AsyncClient(timeout=30) as client:
        # Get SPP document list
        response = await client.get(
            "https://www.ercot.com/misapp/servlets/IceDocListJsonWS",
            params={"reportTypeId": "12301"}  # SPP RT
        )

        data = response.json()
        docs = data.get('ListDocsByRptTypeRes', {}).get('DocumentList', [])

        # Get latest CSV document
        for doc_entry in docs[:5]:
            doc = doc_entry.get('Document', {})
            friendly_name = doc.get('FriendlyName', '')

            if friendly_name.endswith('_csv'):
                doc_id = doc.get('DocID')
                print(f"Inspecting: {friendly_name}")
                print(f"Document ID: {doc_id}")
                print("-" * 70)

                # Download the ZIP file
                download_response = await client.get(
                    "https://www.ercot.com/misdownload/servlets/mirDownload",
                    params={"doclookupId": doc_id}
                )

                # Extract CSV from ZIP
                zip_data = download_response.content

                with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                    filenames = zf.namelist()
                    print(f"Files in ZIP: {filenames}")
                    print()

                    # Find CSV file
                    csv_filename = next((f for f in filenames if f.endswith('.csv')), None)

                    if csv_filename:
                        csv_bytes = zf.read(csv_filename)
                        content = csv_bytes.decode('utf-8')

                        lines = content.split('\n')

                        print(f"Total lines: {len(lines)}")
                        print()
                        print("First 30 lines:")
                        for i, line in enumerate(lines[:30]):
                            print(f"{i+1:3}: {line}")

                break

if __name__ == "__main__":
    asyncio.run(inspect_ercot_csv())
