"""
EPEX Data Ingestion Service
Ingests market data from ENTSOE and stores in Delta tables
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from app.backend.epex.client import EPEXClient
from app.backend.database import execute_sql
from app.backend.config import get_settings


class EPEXIngestionService:
    """Service for ingesting EPEX market data"""

    def __init__(self, api_key: str):
        """
        Initialize EPEX ingestion service

        Args:
            api_key: ENTSOE API security token
        """
        self.client = EPEXClient(api_key)
        self.catalog = get_settings().apex_catalog

    async def close(self):
        """Close the client"""
        await self.client.close()

    async def ingest_day_ahead_prices(
        self,
        market_area: str,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Ingest day-ahead prices for a market area

        Args:
            market_area: Market area code ('DE', 'FR', etc.)
            date: Date to fetch (default: yesterday)

        Returns:
            Ingestion result
        """
        if date is None:
            date = datetime.now() - timedelta(days=1)

        log_id = str(uuid.uuid4())
        start_time = datetime.now()

        try:
            # Fetch from ENTSOE
            end_date = date + timedelta(days=1)
            raw_records = await self.client.get_day_ahead_prices(market_area, date, end_date)

            # Load into Delta table
            records_loaded = await self._load_day_ahead_prices(raw_records)

            # Log success
            duration = (datetime.now() - start_time).total_seconds()
            await self._log_ingestion(
                log_id, 'EPEX', 'DAY_AHEAD_PRICES', date.date(),
                market_area, records_loaded, 0, start_time, 'SUCCESS', duration
            )

            return {
                'status': 'SUCCESS',
                'records_loaded': records_loaded,
                'market_area': market_area,
                'date': date.date().isoformat(),
            }

        except Exception as e:
            # Log failure
            duration = (datetime.now() - start_time).total_seconds()
            await self._log_ingestion(
                log_id, 'EPEX', 'DAY_AHEAD_PRICES', date.date(),
                market_area, 0, 0, start_time, 'FAILED', duration, str(e)
            )
            raise

    async def _load_day_ahead_prices(self, records: List[Dict[str, Any]]) -> int:
        """Load day-ahead price records into Delta table"""
        if not records:
            return 0

        # Build MERGE statement
        values_list = []
        for record in records:
            price_id = str(uuid.uuid4())
            values_list.append(f"""(
                '{price_id}',
                '{record['market_area']}',
                DATE'{record['delivery_date']}',
                {record['delivery_hour']},
                TIMESTAMP'{record['delivery_start']}',
                TIMESTAMP'{record['delivery_end']}',
                {record['price_eur_mwh']},
                {record['volume_mwh'] if record['volume_mwh'] is not None else 'NULL'},
                'ENTSOE',
                CURRENT_TIMESTAMP()
            )""")

        values_str = ',\n'.join(values_list)

        sql = f"""
        MERGE INTO {self.catalog}.market_epex.day_ahead_prices AS target
        USING (
            SELECT * FROM VALUES
            {values_str}
            AS tmp(price_id, market_area, delivery_date, delivery_hour, delivery_start, delivery_end,
                   price_eur_mwh, volume_mwh, data_source, ingestion_timestamp)
        ) AS source
        ON target.market_area = source.market_area
           AND target.delivery_start = source.delivery_start
        WHEN MATCHED THEN
            UPDATE SET
                target.price_eur_mwh = source.price_eur_mwh,
                target.volume_mwh = source.volume_mwh,
                target.ingestion_timestamp = source.ingestion_timestamp
        WHEN NOT MATCHED THEN
            INSERT (price_id, market_area, delivery_date, delivery_hour, delivery_start, delivery_end,
                    price_eur_mwh, volume_mwh, data_source, ingestion_timestamp)
            VALUES (source.price_id, source.market_area, source.delivery_date, source.delivery_hour,
                    source.delivery_start, source.delivery_end, source.price_eur_mwh, source.volume_mwh,
                    source.data_source, source.ingestion_timestamp)
        """

        await execute_sql(sql)
        return len(records)

    async def ingest_generation_forecast(
        self,
        market_area: str,
        fuel_type: str,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Ingest generation forecast for specific fuel type

        Args:
            market_area: Market area code
            fuel_type: 'SOLAR', 'WIND_ONSHORE', etc.
            date: Date to fetch (default: today)

        Returns:
            Ingestion result
        """
        if date is None:
            date = datetime.now()

        log_id = str(uuid.uuid4())
        start_time = datetime.now()

        try:
            # Fetch from ENTSOE
            end_date = date + timedelta(days=1)
            raw_records = await self.client.get_generation_forecast(market_area, fuel_type, date, end_date)

            # Load into Delta table
            records_loaded = await self._load_generation_forecasts(raw_records, fuel_type)

            # Log success
            duration = (datetime.now() - start_time).total_seconds()
            await self._log_ingestion(
                log_id, 'EPEX', f'GEN_FORECAST_{fuel_type}', date.date(),
                market_area, records_loaded, 0, start_time, 'SUCCESS', duration
            )

            return {
                'status': 'SUCCESS',
                'records_loaded': records_loaded,
                'market_area': market_area,
                'fuel_type': fuel_type,
            }

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            await self._log_ingestion(
                log_id, 'EPEX', f'GEN_FORECAST_{fuel_type}', date.date(),
                market_area, 0, 0, start_time, 'FAILED', duration, str(e)
            )
            raise

    async def _load_generation_forecasts(self, records: List[Dict[str, Any]], fuel_type: str) -> int:
        """Load generation forecast records"""
        if not records:
            return 0

        values_list = []
        for record in records:
            forecast_id = str(uuid.uuid4())
            values_list.append(f"""(
                '{forecast_id}',
                '{record['market_area']}',
                TIMESTAMP'{record['forecast_timestamp']}',
                TIMESTAMP'{record['delivery_start']}',
                TIMESTAMP'{record['delivery_end']}',
                '{fuel_type}',
                {record['forecasted_mw']},
                'ENTSOE',
                CURRENT_TIMESTAMP()
            )""")

        values_str = ',\n'.join(values_list)

        sql = f"""
        MERGE INTO {self.catalog}.market_epex.generation_forecasts AS target
        USING (
            SELECT * FROM VALUES
            {values_str}
            AS tmp(forecast_id, market_area, forecast_timestamp, delivery_start, delivery_end,
                   fuel_type, forecasted_mw, forecast_source, ingestion_timestamp)
        ) AS source
        ON target.market_area = source.market_area
           AND target.delivery_start = source.delivery_start
           AND target.fuel_type = source.fuel_type
        WHEN MATCHED THEN
            UPDATE SET
                target.forecasted_mw = source.forecasted_mw,
                target.ingestion_timestamp = source.ingestion_timestamp
        WHEN NOT MATCHED THEN
            INSERT (forecast_id, market_area, forecast_timestamp, delivery_start, delivery_end,
                    fuel_type, forecasted_mw, forecast_source, ingestion_timestamp)
            VALUES (source.forecast_id, source.market_area, source.forecast_timestamp,
                    source.delivery_start, source.delivery_end, source.fuel_type,
                    source.forecasted_mw, source.forecast_source, source.ingestion_timestamp)
        """

        await execute_sql(sql)
        return len(records)

    async def ingest_load_forecast(
        self,
        market_area: str,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Ingest load forecast

        Args:
            market_area: Market area code
            date: Date to fetch (default: today)

        Returns:
            Ingestion result
        """
        if date is None:
            date = datetime.now()

        log_id = str(uuid.uuid4())
        start_time = datetime.now()

        try:
            end_date = date + timedelta(days=2)
            raw_records = await self.client.get_load_forecast(market_area, date, end_date)

            records_loaded = await self._load_demand_forecasts(raw_records)

            duration = (datetime.now() - start_time).total_seconds()
            await self._log_ingestion(
                log_id, 'EPEX', 'LOAD_FORECAST', date.date(),
                market_area, records_loaded, 0, start_time, 'SUCCESS', duration
            )

            return {'status': 'SUCCESS', 'records_loaded': records_loaded}

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            await self._log_ingestion(
                log_id, 'EPEX', 'LOAD_FORECAST', date.date(),
                market_area, 0, 0, start_time, 'FAILED', duration, str(e)
            )
            raise

    async def _load_demand_forecasts(self, records: List[Dict[str, Any]]) -> int:
        """Load demand forecast records"""
        if not records:
            return 0

        values_list = []
        for record in records:
            forecast_id = str(uuid.uuid4())
            values_list.append(f"""(
                '{forecast_id}',
                '{record['market_area']}',
                TIMESTAMP'{record['forecast_timestamp']}',
                TIMESTAMP'{record['delivery_start']}',
                TIMESTAMP'{record['delivery_end']}',
                {record['forecasted_demand_mw']},
                'ENTSOE',
                CURRENT_TIMESTAMP()
            )""")

        values_str = ',\n'.join(values_list)

        sql = f"""
        MERGE INTO {self.catalog}.market_epex.demand_forecasts AS target
        USING (
            SELECT * FROM VALUES
            {values_str}
            AS tmp(forecast_id, market_area, forecast_timestamp, delivery_start, delivery_end,
                   forecasted_demand_mw, forecast_source, ingestion_timestamp)
        ) AS source
        ON target.market_area = source.market_area
           AND target.delivery_start = source.delivery_start
        WHEN MATCHED THEN
            UPDATE SET
                target.forecasted_demand_mw = source.forecasted_demand_mw,
                target.ingestion_timestamp = source.ingestion_timestamp
        WHEN NOT MATCHED THEN
            INSERT (forecast_id, market_area, forecast_timestamp, delivery_start, delivery_end,
                    forecasted_demand_mw, forecast_source, ingestion_timestamp)
            VALUES (source.forecast_id, source.market_area, source.forecast_timestamp,
                    source.delivery_start, source.delivery_end, source.forecasted_demand_mw,
                    source.forecast_source, source.ingestion_timestamp)
        """

        await execute_sql(sql)
        return len(records)

    async def _log_ingestion(
        self,
        log_id: str,
        market_code: str,
        data_type: str,
        date_loaded: Any,
        location: str,
        records_loaded: int,
        records_failed: int,
        start_timestamp: datetime,
        status: str,
        duration_seconds: float,
        error_message: Optional[str] = None
    ):
        """Log ingestion to database"""
        end_timestamp = datetime.now()

        sql = f"""
        INSERT INTO {self.catalog}.core.market_ingestion_log (
            log_id, market_code, data_type, date_loaded, location,
            records_loaded, records_failed, start_timestamp, end_timestamp,
            duration_seconds, status, error_message
        ) VALUES (
            '{log_id}',
            '{market_code}',
            '{data_type}',
            DATE'{date_loaded}',
            '{location}',
            {records_loaded},
            {records_failed},
            TIMESTAMP'{start_timestamp}',
            TIMESTAMP'{end_timestamp}',
            {duration_seconds},
            '{status}',
            {f"'{error_message}'" if error_message else 'NULL'}
        )
        """

        await execute_sql(sql)


# Singleton accessor
_epex_service: Optional[EPEXIngestionService] = None


def get_epex_ingestion_service() -> EPEXIngestionService:
    """Get EPEX ingestion service singleton"""
    global _epex_service
    if _epex_service is None:
        # API key should come from config/environment
        api_key = get_settings().entsoe_api_key
        _epex_service = EPEXIngestionService(api_key)
    return _epex_service
