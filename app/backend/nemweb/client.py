"""
NEMWEB API Client
Fetches data from AEMO's NEMWEB portal (Australian Energy Market Operator)
"""
from __future__ import annotations

import io
import zipfile
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import csv
import httpx
from pathlib import Path


class NEMWEBClient:
    """
    Client for AEMO NEMWEB data portal

    Data types:
    - Dispatch prices (5-minute intervals)
    - Pre-dispatch forecasts
    - Trading prices (30-minute intervals)
    - Demand actuals
    - Generation by fuel type
    - Interconnector flows
    """

    BASE_URL = "https://nemweb.com.au/Reports/Current"
    ARCHIVE_URL = "https://nemweb.com.au/Reports/Archive"

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Initialize NEMWEB client

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def get_dispatch_prices(
        self,
        date: Optional[datetime] = None,
        regions: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get 5-minute dispatch prices

        NEMWEB Path: /PUBLIC_PRICES/PRICES_{YYYYMMDD}_{file}.zip

        Args:
            date: Date to fetch (default: today)
            regions: Filter by regions (NSW1, VIC1, QLD1, SA1, TAS1)

        Returns:
            List of dispatch price records
        """
        if date is None:
            date = datetime.now()

        # Format: PRICES_20260322_20260322143000.zip
        date_str = date.strftime("%Y%m%d")

        # Construct URL - NEMWEB provides current day dispatch prices
        url = f"{self.BASE_URL}/Dispatch_SCADA/PUBLIC_PRICES_{date_str}.zip"

        try:
            # Fetch and parse
            records = await self._fetch_and_parse_zip(url)

            # Filter dispatch prices (not pre-dispatch or forecast)
            dispatch_records = [
                r for r in records
                if r.get('INTERVENTION') == '0'  # Non-intervention
            ]

            # Filter by regions if specified
            if regions:
                dispatch_records = [
                    r for r in dispatch_records
                    if r.get('REGIONID') in regions
                ]

            return dispatch_records

        except Exception as e:
            print(f"Error fetching dispatch prices: {e}")
            return []

    async def get_predispatch_forecast(
        self,
        region_id: str = 'NSW1',
        hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """
        Get pre-dispatch price forecasts (up to 40 hours ahead)

        NEMWEB Path: /PUBLIC_PREDISPATCH/PREDISPATCH_{YYYYMMDD}_{file}.zip

        Args:
            region_id: Region (NSW1, VIC1, QLD1, SA1, TAS1)
            hours: Forecast horizon in hours

        Returns:
            List of forecast records
        """
        date = datetime.now()
        date_str = date.strftime("%Y%m%d")

        url = f"{self.BASE_URL}/PredispatchIS_Reports/PUBLIC_PREDISPATCH_{date_str}.zip"

        try:
            records = await self._fetch_and_parse_zip(url)

            # Filter by region and forecast horizon
            cutoff = date + timedelta(hours=hours)

            forecasts = [
                r for r in records
                if r.get('REGIONID') == region_id
                and self._parse_datetime(r.get('DATETIME')) <= cutoff
            ]

            return forecasts

        except Exception as e:
            print(f"Error fetching predispatch forecast: {e}")
            return []

    async def get_demand_actual(
        self,
        region_id: str = 'NSW1',
        date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get actual demand data

        NEMWEB Path: /PUBLIC_DISPATCHLOAD/

        Args:
            region_id: Region ID
            date: Date to fetch

        Returns:
            List of demand records
        """
        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y%m%d")

        url = f"{self.BASE_URL}/Dispatch_SCADA/PUBLIC_DISPATCHLOAD_{date_str}.zip"

        try:
            records = await self._fetch_and_parse_zip(url)

            demand_records = [
                r for r in records
                if r.get('REGIONID') == region_id
            ]

            return demand_records

        except Exception as e:
            print(f"Error fetching demand actual: {e}")
            return []

    async def get_generation_by_fuel_type(
        self,
        date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get generation by fuel type

        NEMWEB Path: /PUBLIC_ROOFTOP_PV/ or derived from dispatch data

        Args:
            date: Date to fetch

        Returns:
            List of generation records by fuel type
        """
        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y%m%d")

        # Try rooftop PV data first
        url = f"{self.BASE_URL}/Dispatch_SCADA/PUBLIC_ROOFTOP_PV_{date_str}.zip"

        try:
            records = await self._fetch_and_parse_zip(url)
            return records

        except Exception as e:
            print(f"Error fetching generation data: {e}")
            return []

    async def get_historical_prices(
        self,
        start_date: datetime,
        end_date: datetime,
        region_id: str = 'NSW1',
    ) -> List[Dict[str, Any]]:
        """
        Get historical dispatch prices for date range

        Used for backtesting and historical analysis

        Args:
            start_date: Start date
            end_date: End date
            region_id: Region ID

        Returns:
            List of historical price records
        """
        all_records = []
        current_date = start_date

        while current_date <= end_date:
            try:
                date_str = current_date.strftime("%Y%m%d")

                # Historical data is in archive
                url = f"{self.ARCHIVE_URL}/Dispatch_SCADA/PUBLIC_PRICES_{date_str}.zip"

                records = await self._fetch_and_parse_zip(url)

                # Filter by region
                region_records = [
                    r for r in records
                    if r.get('REGIONID') == region_id
                ]

                all_records.extend(region_records)

                print(f"Fetched {len(region_records)} records for {date_str}")

            except Exception as e:
                print(f"Error fetching historical data for {current_date}: {e}")

            current_date += timedelta(days=1)

        return all_records

    async def _fetch_and_parse_zip(self, url: str) -> List[Dict[str, Any]]:
        """
        Fetch ZIP file from NEMWEB and parse CSV contents

        Args:
            url: NEMWEB URL

        Returns:
            List of parsed records
        """
        # Fetch with retries
        for attempt in range(self.max_retries):
            try:
                response = await self.client.get(url)
                response.raise_for_status()

                # Parse ZIP file
                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    # Find CSV file (usually only one)
                    csv_files = [f for f in z.namelist() if f.endswith('.CSV')]

                    if not csv_files:
                        print(f"No CSV files found in {url}")
                        return []

                    # Parse first CSV
                    csv_file = csv_files[0]
                    with z.open(csv_file) as f:
                        content = f.read().decode('utf-8')
                        return self._parse_aemo_csv(content)

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    # File not available (common for future dates or missing data)
                    return []

                if attempt < self.max_retries - 1:
                    print(f"HTTP error {e.response.status_code}, retrying... ({attempt + 1}/{self.max_retries})")
                    continue
                else:
                    raise

            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"Error fetching {url}, retrying... ({attempt + 1}/{self.max_retries})")
                    continue
                else:
                    raise

        return []

    def _parse_aemo_csv(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse AEMO CSV format

        AEMO CSV has specific format:
        - First row: C (comment) with metadata
        - Second row: I (info) with column headers
        - Data rows: D (data)

        Args:
            content: CSV content string

        Returns:
            List of dictionaries (one per data row)
        """
        records = []
        headers = None

        for line in content.splitlines():
            if not line.strip():
                continue

            parts = line.split(',')

            if not parts:
                continue

            record_type = parts[0]

            if record_type == 'I':
                # Header row - extract column names
                # Format: I,TABLE_NAME,column1,column2,...
                headers = [h.strip('"') for h in parts[2:]]  # Skip 'I' and table name

            elif record_type == 'D':
                # Data row
                if headers is None:
                    continue

                # Format: D,TABLE_NAME,value1,value2,...
                values = [v.strip('"') for v in parts[2:]]  # Skip 'D' and table name

                # Create dictionary
                record = {}
                for i, header in enumerate(headers):
                    if i < len(values):
                        record[header] = values[i]

                records.append(record)

        return records

    def _parse_datetime(self, datetime_str: str) -> datetime:
        """Parse AEMO datetime format"""
        try:
            # AEMO format: YYYY/MM/DD HH:MM:SS
            return datetime.strptime(datetime_str, "%Y/%m/%d %H:%M:%S")
        except:
            try:
                # Alternative format: YYYYMMDDHHMMSS
                return datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
            except:
                return datetime.now()

    def _format_price_record(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format raw NEMWEB price record to standardized format

        Args:
            raw: Raw record from NEMWEB

        Returns:
            Standardized price record
        """
        return {
            'interval_datetime': self._parse_datetime(raw.get('SETTLEMENTDATE', '')),
            'region_id': raw.get('REGIONID', ''),
            'rrp': float(raw.get('RRP', 0)),  # Regional Reference Price
            'demand_mw': float(raw.get('TOTALDEMAND', 0)),
            'intervention': raw.get('INTERVENTION', '0') == '1',
        }


# Singleton instance
_client: Optional[NEMWEBClient] = None


async def get_nemweb_client() -> NEMWEBClient:
    """Get NEMWEB client singleton"""
    global _client
    if _client is None:
        _client = NEMWEBClient()
    return _client


async def close_nemweb_client():
    """Close NEMWEB client"""
    global _client
    if _client is not None:
        await _client.close()
        _client = None
