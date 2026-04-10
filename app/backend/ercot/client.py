"""
ERCOT (Electric Reliability Council of Texas) Public Data Client
Fetches market data from ERCOT Public Data Portal (Mis-Reports)
"""
from __future__ import annotations

import asyncio
import io
import zipfile
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import csv
import xml.etree.ElementTree as ET

import httpx


class ERCOTClient:
    """
    Client for fetching ERCOT market data from public portal

    Uses ERCOT's Mis-Reports servlet - no API key required!

    ERCOT provides:
    - Real-time Settlement Point Prices (SPP) - 5-minute intervals
    - Day-Ahead Market prices (DAM) - 15-minute intervals
    - Load forecasts
    - Wind/Solar generation data
    """

    # ERCOT Public Data Portal (Mis-Reports)
    MIS_REPORTS_URL = "https://www.ercot.com/misapp/servlets/IceDocListJsonWS"
    MIS_DOWNLOAD_URL = "https://www.ercot.com/misdownload/servlets/mirDownload"

    # Report Type IDs
    REPORT_TYPES = {
        'SPP_RT': '12301',  # Settlement Point Prices (Real-Time)
        'DAM_PRICES': '12329',  # Historical DAM Load Zone and Hub Prices
        'RTM_PRICES': '13114',  # Historical RTM Load Zone and Hub Prices
        'DAM_DISCLOSURE': '13101',  # 60-Day DAM Disclosure Reports
        'SCED_DISCLOSURE': '13060',  # 60-Day SCED Disclosure Reports
    }

    # Major settlement points (hubs)
    SETTLEMENT_POINTS = {
        'HB_NORTH': 'LZ_NORTH',
        'HB_SOUTH': 'LZ_SOUTH',
        'HB_WEST': 'LZ_WEST',
        'HB_HOUSTON': 'LZ_HOUSTON',
        'HB_BUSAVG': 'LZ_HOUSTON',  # System average often maps to Houston zone
        'HB_PAN': 'LZ_WEST',  # Panhandle typically in West zone
    }

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """
        Initialize ERCOT client

        Args:
            api_key: Not used for public portal (kept for compatibility)
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self._document_cache: Dict[str, Any] = {}

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def _get_report_documents(
        self,
        report_type: str,
        max_docs: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get list of available documents for a report type

        Args:
            report_type: Report type key (e.g., 'SPP_RT')
            max_docs: Maximum documents to return

        Returns:
            List of document metadata
        """
        report_id = self.REPORT_TYPES.get(report_type)
        if not report_id:
            raise ValueError(f"Unknown report type: {report_type}")

        # Check cache
        cache_key = f"{report_type}_{max_docs}"
        if cache_key in self._document_cache:
            cached_time, cached_docs = self._document_cache[cache_key]
            if (datetime.now() - cached_time).seconds < 300:  # 5 min cache
                return cached_docs

        try:
            response = await self.client.get(
                self.MIS_REPORTS_URL,
                params={"reportTypeId": report_id}
            )
            response.raise_for_status()

            data = response.json()
            doc_list = data.get('ListDocsByRptTypeRes', {}).get('DocumentList', [])

            # Extract document info
            documents = []
            for doc_entry in doc_list[:max_docs]:
                doc = doc_entry.get('Document', {})
                documents.append({
                    'doc_id': doc.get('DocID'),
                    'friendly_name': doc.get('FriendlyName', ''),
                    'publish_date': doc.get('PublishDate'),
                    'construction_date': doc.get('ConstructedDate'),
                })

            # Cache results
            self._document_cache[cache_key] = (datetime.now(), documents)

            return documents

        except Exception as e:
            print(f"Error fetching report documents for {report_type}: {e}")
            return []

    async def _download_document(self, doc_id: str) -> str:
        """
        Download and extract document content by ID

        ERCOT serves files as ZIP archives - extract and return CSV content

        Args:
            doc_id: Document ID from report list

        Returns:
            Document content as string (CSV)
        """
        try:
            # Use doclookupId parameter (exact spelling from ERCOT API)
            response = await self.client.get(
                self.MIS_DOWNLOAD_URL,
                params={"doclookupId": doc_id}
            )
            response.raise_for_status()

            # ERCOT serves files as ZIP archives
            # Extract the CSV file from the ZIP
            zip_data = response.content

            with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                # Get list of files in ZIP
                filenames = zf.namelist()

                # Find the CSV file (usually the only file)
                csv_filename = next((f for f in filenames if f.endswith('.csv')), None)

                if csv_filename:
                    # Read and decode the CSV
                    csv_bytes = zf.read(csv_filename)
                    return csv_bytes.decode('utf-8')
                else:
                    print(f"No CSV file found in ZIP archive: {filenames}")
                    return ""

        except zipfile.BadZipFile:
            # Not a ZIP file - return as-is (fallback)
            return response.text
        except Exception as e:
            print(f"Error downloading/extracting document {doc_id}: {e}")
            return ""

    async def _parse_spp_csv(self, csv_content: str) -> List[Dict[str, Any]]:
        """
        Parse SPP CSV content into structured records

        ERCOT CSV format:
        DeliveryDate,DeliveryHour,DeliveryInterval,SettlementPointName,SettlementPointType,SettlementPointPrice,DSTFlag

        Args:
            csv_content: CSV file content

        Returns:
            List of price records
        """
        records = []

        try:
            reader = csv.DictReader(io.StringIO(csv_content))

            for row in reader:
                try:
                    # Parse timestamp
                    delivery_date = row.get('DeliveryDate', '')
                    delivery_hour = row.get('DeliveryHour', '')
                    delivery_interval = row.get('DeliveryInterval', '')

                    if not all([delivery_date, delivery_hour, delivery_interval]):
                        continue

                    # Convert ERCOT interval format:
                    # Intervals are 1-4 (15-min) or 1-12 (5-min)
                    # Hour is 1-24
                    # Convert to actual minute
                    hour = int(delivery_hour) - 1  # Convert to 0-23
                    interval_num = int(delivery_interval)
                    minute = (interval_num - 1) * 5  # 5-minute intervals

                    # Create datetime
                    delivery_dt = datetime.strptime(delivery_date, "%m/%d/%Y")
                    interval_datetime = delivery_dt.replace(hour=hour, minute=minute)

                    # Extract settlement point name
                    settlement_point_name = row.get('SettlementPointName', '')

                    # Extract prices
                    spp = row.get('SettlementPointPrice', '0')

                    records.append({
                        'settlement_point': settlement_point_name,
                        'interval_datetime': interval_datetime,
                        'spp_usd_mwh': float(spp) if spp else 0.0,
                        'congestion_price_usd_mwh': 0.0,  # May not be in all reports
                        'loss_price_usd_mwh': 0.0,  # May not be in all reports
                    })

                except (ValueError, KeyError) as e:
                    # Skip malformed rows
                    continue

        except Exception as e:
            print(f"Error parsing SPP CSV: {e}")

        return records

    async def _parse_dam_csv(self, csv_content: str) -> List[Dict[str, Any]]:
        """
        Parse DAM prices CSV content

        Args:
            csv_content: CSV file content

        Returns:
            List of DAM price records
        """
        records = []

        try:
            reader = csv.DictReader(io.StringIO(csv_content))

            for row in reader:
                try:
                    # Parse delivery datetime
                    delivery_date_str = row.get('DeliveryDate', row.get('Delivery Date', ''))
                    hour_ending = row.get('HourEnding', row.get('Hour Ending', ''))

                    if not all([delivery_date_str, hour_ending]):
                        continue

                    # Parse date and hour
                    delivery_date = datetime.strptime(delivery_date_str, "%m/%d/%Y").date()
                    delivery_hour = int(hour_ending.split(':')[0])

                    # Construct delivery_start timestamp
                    delivery_start = datetime.combine(
                        delivery_date,
                        datetime.min.time()
                    ) + timedelta(hours=delivery_hour - 1)

                    # Extract settlement point
                    settlement_point = row.get('SettlementPoint', row.get('Settlement Point', ''))

                    # Extract prices
                    lmp = row.get('SettlementPointPrice', row.get('LMP', '0'))

                    records.append({
                        'settlement_point': settlement_point,
                        'delivery_date': delivery_date,
                        'delivery_hour': delivery_hour,
                        'delivery_interval': 1,  # DAM is hourly
                        'delivery_start': delivery_start,
                        'lmp_usd_mwh': float(lmp) if lmp else 0.0,
                        'energy_price_usd_mwh': 0.0,
                        'congestion_price_usd_mwh': 0.0,
                        'loss_price_usd_mwh': 0.0,
                    })

                except (ValueError, KeyError) as e:
                    continue

        except Exception as e:
            print(f"Error parsing DAM CSV: {e}")

        return records

    async def get_real_time_prices(
        self,
        settlement_point: str,
        start_datetime: datetime,
        end_datetime: datetime
    ) -> List[Dict[str, Any]]:
        """
        Fetch real-time Settlement Point Prices (SPP)

        Args:
            settlement_point: Settlement point code (e.g., 'HB_NORTH')
            start_datetime: Start datetime
            end_datetime: End datetime

        Returns:
            List of price records (5-minute intervals)
        """
        # Get most recent SPP documents
        documents = await self._get_report_documents('SPP_RT', max_docs=10)

        if not documents:
            print("No SPP documents available")
            return []

        all_records = []

        # Try downloading recent documents until we have data in our time range
        for doc in documents[:5]:  # Check last 5 documents
            doc_id = doc.get('doc_id')
            friendly_name = doc.get('friendly_name', '')

            # Only process CSV files
            if not friendly_name.endswith('_csv'):
                continue

            print(f"Downloading SPP data: {friendly_name}")

            content = await self._download_document(doc_id)
            if not content:
                continue

            # Parse CSV content
            records = await self._parse_spp_csv(content)

            # Filter by settlement point and time range
            filtered_records = [
                r for r in records
                if r['settlement_point'] == settlement_point
                and start_datetime <= r['interval_datetime'] <= end_datetime
            ]

            all_records.extend(filtered_records)

            # If we have enough data, stop downloading more documents
            if len(all_records) >= 12:  # At least 1 hour of 5-min data
                break

        # Sort by datetime
        all_records.sort(key=lambda x: x['interval_datetime'], reverse=True)

        return all_records

    async def get_day_ahead_prices(
        self,
        settlement_point: str,
        delivery_date: datetime.date
    ) -> List[Dict[str, Any]]:
        """
        Fetch Day-Ahead Market (DAM) prices

        Args:
            settlement_point: Settlement point code
            delivery_date: Delivery date

        Returns:
            List of price records
        """
        # Get DAM price documents
        documents = await self._get_report_documents('DAM_PRICES', max_docs=10)

        if not documents:
            print("No DAM documents available")
            return []

        all_records = []

        # Download and parse recent documents
        for doc in documents[:3]:
            doc_id = doc.get('doc_id')
            friendly_name = doc.get('friendly_name', '')

            # Only process CSV files
            if not friendly_name.endswith('_csv'):
                continue

            print(f"Downloading DAM data: {friendly_name}")

            content = await self._download_document(doc_id)
            if not content:
                continue

            # Parse CSV
            records = await self._parse_dam_csv(content)

            # Filter by settlement point and delivery date
            filtered_records = [
                r for r in records
                if r['settlement_point'] == settlement_point
                and r['delivery_date'] == delivery_date
            ]

            all_records.extend(filtered_records)

            if all_records:
                break  # Found data for this date

        return all_records

    async def get_load_forecast(
        self,
        forecast_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Fetch system load forecast

        Note: Load forecasts may require different report types

        Args:
            forecast_type: 'SHORT_TERM', 'MID_TERM', or 'LONG_TERM'
            start_date: Start date
            end_date: End date

        Returns:
            List of load forecast records
        """
        # Load forecasts would need specific report type IDs
        # This is a placeholder - implement when report IDs are known
        print(f"Load forecast not yet implemented for public portal")
        return []

    async def get_renewable_generation(
        self,
        fuel_type: str,
        date: datetime.date
    ) -> List[Dict[str, Any]]:
        """
        Fetch actual renewable generation (wind/solar)

        Args:
            fuel_type: 'WIND' or 'SOLAR'
            date: Date to fetch

        Returns:
            List of generation records
        """
        # Renewable generation would need specific report type IDs
        # This is a placeholder
        print(f"{fuel_type} generation not yet implemented for public portal")
        return []


async def main():
    """Example usage"""
    client = ERCOTClient()

    try:
        # Fetch real-time prices for yesterday (most recent complete data)
        # ERCOT data has a lag, so query yesterday's data
        yesterday = datetime.now() - timedelta(days=1)
        start_datetime = yesterday.replace(hour=18, minute=0, second=0)  # 6 PM
        end_datetime = yesterday.replace(hour=22, minute=0, second=0)    # 10 PM

        print("=" * 70)
        print("ERCOT Public Portal Client Test")
        print("=" * 70)
        print()
        print("Fetching ERCOT real-time prices for Houston Hub...")
        print(f"Settlement Point: LZ_HOUSTON")
        print(f"Time range: {start_datetime} to {end_datetime}")
        print()

        prices = await client.get_real_time_prices('LZ_HOUSTON', start_datetime, end_datetime)

        print(f"✅ Retrieved {len(prices)} price records")
        if prices:
            print()
            print("Latest 5 prices:")
            for p in prices[:5]:
                print(f"  {p['interval_datetime']}: ${p['spp_usd_mwh']:.2f}/MWh")
        else:
            print("⚠️  No data found for this time range")
            print("   Try adjusting the date/time to match available data")

        print()
        print("-" * 70)
        print()

        # Also try HB_HOUSTON (hub average)
        print("Fetching hub average prices...")
        print(f"Settlement Point: HB_HOUSTON")
        print()

        hub_prices = await client.get_real_time_prices('HB_HOUSTON', start_datetime, end_datetime)

        print(f"✅ Retrieved {len(hub_prices)} hub price records")
        if hub_prices:
            print()
            print("Latest 5 hub prices:")
            for p in hub_prices[:5]:
                print(f"  {p['interval_datetime']}: ${p['spp_usd_mwh']:.2f}/MWh")

        print()
        print("=" * 70)
        print("Test Complete!")
        print("=" * 70)

    finally:
        await client.close()


if __name__ == '__main__':
    asyncio.run(main())
