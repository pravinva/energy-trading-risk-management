"""
EPEX (European Power Exchange) API Client
Fetches market data from ENTSOE Transparency Platform and EPEX SPOT
"""
from __future__ import annotations

import asyncio
import io
import zipfile
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import xml.etree.ElementTree as ET

import httpx

class EPEXClient:
    """
    Client for fetching EPEX market data from ENTSOE Transparency Platform

    ENTSOE API provides:
    - Day-ahead prices
    - Intraday prices
    - Generation forecasts (wind, solar, etc.)
    - Load forecasts
    - Cross-border flows
    """

    BASE_URL = "https://transparency.entsoe.eu/api"

    # EIC codes for major European bidding zones
    MARKET_AREAS = {
        'DE': '10Y1001A1001A83F',  # Germany/Luxembourg
        'FR': '10YFR-RTE------C',   # France
        'AT': '10YAT-APG------L',   # Austria
        'NL': '10YNL----------L',   # Netherlands
        'BE': '10YBE----------2',   # Belgium
        'CH': '10YCH-SWISSGRIDZ',   # Switzerland
        'IT_NORD': '10Y1001A1001A73I',  # Italy North
        'ES': '10YES-REE------0',   # Spain
        'DK1': '10YDK-1--------W',  # Denmark West
        'DK2': '10YDK-2--------M',  # Denmark East
    }

    def __init__(self, api_key: str, timeout: int = 30):
        """
        Initialize EPEX client

        Args:
            api_key: ENTSOE API security token
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def _make_request(self, params: Dict[str, str]) -> str:
        """
        Make request to ENTSOE API

        Args:
            params: Query parameters

        Returns:
            XML response as string
        """
        params['securityToken'] = self.api_key

        try:
            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            print(f"HTTP error fetching ENTSOE data: {e}")
            raise
        except Exception as e:
            print(f"Error fetching ENTSOE data: {e}")
            raise

    def _parse_timeseries_xml(self, xml_content: str) -> List[Dict[str, Any]]:
        """
        Parse ENTSOE XML timeseries response

        Args:
            xml_content: XML response string

        Returns:
            List of parsed records
        """
        try:
            root = ET.fromstring(xml_content)
            namespace = {'ns': 'urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0'}

            records = []

            for timeseries in root.findall('.//ns:TimeSeries', namespace):
                # Extract period info
                for period in timeseries.findall('.//ns:Period', namespace):
                    start_str = period.find('.//ns:timeInterval/ns:start', namespace).text
                    start_time = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                    resolution = period.find('.//ns:resolution', namespace).text

                    # Parse resolution (e.g., 'PT60M' = 60 minutes)
                    resolution_minutes = self._parse_resolution(resolution)

                    # Extract data points
                    for point in period.findall('.//ns:Point', namespace):
                        position = int(point.find('.//ns:position', namespace).text)
                        value_elem = point.find('.//ns:price.amount', namespace)
                        if value_elem is None:
                            value_elem = point.find('.//ns:quantity', namespace)

                        if value_elem is not None:
                            value = float(value_elem.text)

                            # Calculate timestamp for this point
                            point_time = start_time + timedelta(minutes=(position - 1) * resolution_minutes)

                            records.append({
                                'timestamp': point_time,
                                'value': value,
                                'resolution_minutes': resolution_minutes,
                                'position': position,
                            })

            return records
        except Exception as e:
            print(f"Error parsing ENTSOE XML: {e}")
            return []

    def _parse_resolution(self, resolution: str) -> int:
        """Parse ISO 8601 duration to minutes"""
        # PT60M = 60 minutes, PT15M = 15 minutes, P1D = 1 day, etc.
        if resolution == 'PT15M':
            return 15
        elif resolution == 'PT60M':
            return 60
        elif resolution == 'P1D':
            return 1440
        else:
            # Generic parser for PTnM or PTnH
            if 'M' in resolution:
                return int(resolution.replace('PT', '').replace('M', ''))
            elif 'H' in resolution:
                return int(resolution.replace('PT', '').replace('H', '')) * 60
            return 60  # Default to hourly

    async def get_day_ahead_prices(
        self,
        market_area: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Fetch day-ahead auction prices

        Args:
            market_area: Market area code ('DE', 'FR', etc.)
            start_date: Start date
            end_date: End date

        Returns:
            List of price records
        """
        eic_code = self.MARKET_AREAS.get(market_area)
        if not eic_code:
            raise ValueError(f"Unknown market area: {market_area}")

        params = {
            'documentType': 'A44',  # Price document
            'in_Domain': eic_code,
            'out_Domain': eic_code,
            'periodStart': start_date.strftime('%Y%m%d0000'),
            'periodEnd': end_date.strftime('%Y%m%d0000'),
        }

        xml_response = await self._make_request(params)
        raw_records = self._parse_timeseries_xml(xml_response)

        # Transform to standard format
        records = []
        for record in raw_records:
            timestamp = record['timestamp']
            records.append({
                'market_area': market_area,
                'delivery_date': timestamp.date(),
                'delivery_hour': timestamp.hour + 1,  # 1-24
                'delivery_start': timestamp,
                'delivery_end': timestamp + timedelta(minutes=record['resolution_minutes']),
                'price_eur_mwh': record['value'],
                'volume_mwh': None,  # Volume not in this document type
            })

        return records

    async def get_generation_forecast(
        self,
        market_area: str,
        fuel_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Fetch generation forecast for specific fuel type

        Args:
            market_area: Market area code
            fuel_type: 'SOLAR', 'WIND_ONSHORE', 'WIND_OFFSHORE', 'NUCLEAR', etc.
            start_date: Start date
            end_date: End date

        Returns:
            List of forecast records
        """
        eic_code = self.MARKET_AREAS.get(market_area)
        if not eic_code:
            raise ValueError(f"Unknown market area: {market_area}")

        # Map fuel type to ENTSOE PSR type
        psr_type_map = {
            'SOLAR': 'B16',
            'WIND_ONSHORE': 'B18',
            'WIND_OFFSHORE': 'B19',
            'NUCLEAR': 'B14',
            'HYDRO': 'B12',
            'GAS': 'B04',
        }
        psr_type = psr_type_map.get(fuel_type, 'B16')

        params = {
            'documentType': 'A69',  # Generation forecast
            'processType': 'A01',  # Day ahead
            'in_Domain': eic_code,
            'periodStart': start_date.strftime('%Y%m%d0000'),
            'periodEnd': end_date.strftime('%Y%m%d0000'),
            'PsrType': psr_type,
        }

        xml_response = await self._make_request(params)
        raw_records = self._parse_timeseries_xml(xml_response)

        # Transform to standard format
        records = []
        for record in raw_records:
            timestamp = record['timestamp']
            records.append({
                'market_area': market_area,
                'forecast_timestamp': datetime.now(),
                'delivery_start': timestamp,
                'delivery_end': timestamp + timedelta(minutes=record['resolution_minutes']),
                'fuel_type': fuel_type,
                'forecasted_mw': record['value'],
            })

        return records

    async def get_load_forecast(
        self,
        market_area: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Fetch load (demand) forecast

        Args:
            market_area: Market area code
            start_date: Start date
            end_date: End date

        Returns:
            List of forecast records
        """
        eic_code = self.MARKET_AREAS.get(market_area)
        if not eic_code:
            raise ValueError(f"Unknown market area: {market_area}")

        params = {
            'documentType': 'A65',  # Load forecast
            'processType': 'A01',  # Day ahead
            'outBiddingZone_Domain': eic_code,
            'periodStart': start_date.strftime('%Y%m%d0000'),
            'periodEnd': end_date.strftime('%Y%m%d0000'),
        }

        xml_response = await self._make_request(params)
        raw_records = self._parse_timeseries_xml(xml_response)

        # Transform to standard format
        records = []
        for record in raw_records:
            timestamp = record['timestamp']
            records.append({
                'market_area': market_area,
                'forecast_timestamp': datetime.now(),
                'delivery_start': timestamp,
                'delivery_end': timestamp + timedelta(minutes=record['resolution_minutes']),
                'forecasted_demand_mw': record['value'],
            })

        return records

    async def get_cross_border_flows(
        self,
        from_area: str,
        to_area: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Fetch cross-border electricity flows

        Args:
            from_area: Source market area
            to_area: Destination market area
            start_date: Start date
            end_date: End date

        Returns:
            List of flow records
        """
        from_eic = self.MARKET_AREAS.get(from_area)
        to_eic = self.MARKET_AREAS.get(to_area)

        if not from_eic or not to_eic:
            raise ValueError(f"Unknown market areas: {from_area} or {to_area}")

        params = {
            'documentType': 'A11',  # Aggregated energy data report
            'in_Domain': from_eic,
            'out_Domain': to_eic,
            'periodStart': start_date.strftime('%Y%m%d0000'),
            'periodEnd': end_date.strftime('%Y%m%d0000'),
        }

        xml_response = await self._make_request(params)
        raw_records = self._parse_timeseries_xml(xml_response)

        # Transform to standard format
        records = []
        for record in raw_records:
            timestamp = record['timestamp']
            records.append({
                'from_area': from_area,
                'to_area': to_area,
                'timestamp': timestamp,
                'scheduled_flow_mw': record['value'],
                'actual_flow_mw': record['value'],  # Same for this document type
                'capacity_mw': None,
            })

        return records

    async def get_intraday_prices(
        self,
        market_area: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Fetch intraday continuous trading prices (if available via API)

        Note: Intraday continuous is harder to get via ENTSOE API.
        This may require direct EPEX SPOT API integration.

        Args:
            market_area: Market area code
            start_date: Start date
            end_date: End date

        Returns:
            List of intraday trade records
        """
        # Placeholder - intraday continuous requires specific EPEX API
        # For now, return empty list or implement with EPEX-specific endpoint
        print(f"Intraday prices not yet implemented for {market_area}")
        return []


async def main():
    """Example usage"""
    # API key should be stored in environment variable
    api_key = "YOUR_ENTSOE_API_KEY"

    client = EPEXClient(api_key)

    try:
        # Fetch German day-ahead prices for yesterday
        end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=1)

        print("Fetching German day-ahead prices...")
        prices = await client.get_day_ahead_prices('DE', start_date, end_date)
        print(f"Retrieved {len(prices)} price records")
        if prices:
            print(f"Sample: {prices[0]}")

        # Fetch wind generation forecast
        print("\nFetching German wind generation forecast...")
        wind_forecast = await client.get_generation_forecast('DE', 'WIND_ONSHORE', start_date, end_date)
        print(f"Retrieved {len(wind_forecast)} forecast records")
        if wind_forecast:
            print(f"Sample: {wind_forecast[0]}")

        # Fetch load forecast
        print("\nFetching German load forecast...")
        load_forecast = await client.get_load_forecast('DE', start_date, end_date)
        print(f"Retrieved {len(load_forecast)} load forecast records")

    finally:
        await client.close()


if __name__ == '__main__':
    asyncio.run(main())
