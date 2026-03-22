"""
ERCOT Data Ingestion Service
Real-time ingestion of ERCOT market data (5-minute intervals)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from app.backend.ercot.client import ERCOTClient
from app.backend.database import execute_sql
from app.backend.config import get_settings


class ERCOTIngestionService:
    """Service for real-time ERCOT market data ingestion"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ERCOT ingestion service

        Args:
            api_key: ERCOT API key (optional for public data)
        """
        self.client = ERCOTClient(api_key)
        self.catalog = get_settings().apex_catalog

    async def close(self):
        """Close the client"""
        await self.client.close()

    async def ingest_real_time_prices(
        self,
        settlement_point: str = 'HB_BUSAVG',
        lookback_hours: int = 1
    ) -> Dict[str, Any]:
        """
        Ingest real-time Settlement Point Prices (5-minute intervals)

        Args:
            settlement_point: Settlement point code (default: system average)
            lookback_hours: How many hours back to fetch

        Returns:
            Ingestion result
        """
        log_id = str(uuid.uuid4())
        start_time = datetime.now()
        end_datetime = datetime.now()
        start_datetime = end_datetime - timedelta(hours=lookback_hours)

        try:
            # Fetch real-time prices (5-minute SPP)
            raw_records = await self.client.get_real_time_prices(
                settlement_point, start_datetime, end_datetime
            )

            # Load into Delta table
            records_loaded = await self._load_real_time_prices(raw_records)

            # Log success
            duration = (datetime.now() - start_time).total_seconds()
            await self._log_ingestion(
                log_id, 'ERCOT', 'REAL_TIME_PRICES', start_datetime.date(),
                settlement_point, records_loaded, 0, start_time, 'SUCCESS', duration
            )

            return {
                'status': 'SUCCESS',
                'records_loaded': records_loaded,
                'settlement_point': settlement_point,
                'interval': '5-minute',
            }

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            await self._log_ingestion(
                log_id, 'ERCOT', 'REAL_TIME_PRICES', start_datetime.date(),
                settlement_point, 0, 0, start_time, 'FAILED', duration, str(e)
            )
            raise

    async def _load_real_time_prices(self, records: List[Dict[str, Any]]) -> int:
        """Load real-time price records into Delta table"""
        if not records:
            return 0

        values_list = []
        for record in records:
            spp_id = str(uuid.uuid4())
            values_list.append(f"""(
                '{spp_id}',
                '{record['settlement_point']}',
                TIMESTAMP'{record['interval_datetime']}',
                {record['spp_usd_mwh']},
                {record['congestion_price_usd_mwh']},
                {record['loss_price_usd_mwh']},
                'ERCOT',
                CURRENT_TIMESTAMP()
            )""")

        values_str = ',\n'.join(values_list)

        sql = f"""
        MERGE INTO {self.catalog}.market_ercot.real_time_prices AS target
        USING (
            SELECT * FROM VALUES
            {values_str}
            AS tmp(spp_id, settlement_point, interval_datetime, spp_usd_mwh,
                   congestion_price_usd_mwh, loss_price_usd_mwh, data_source, ingestion_timestamp)
        ) AS source
        ON target.settlement_point = source.settlement_point
           AND target.interval_datetime = source.interval_datetime
        WHEN MATCHED THEN
            UPDATE SET
                target.spp_usd_mwh = source.spp_usd_mwh,
                target.congestion_price_usd_mwh = source.congestion_price_usd_mwh,
                target.loss_price_usd_mwh = source.loss_price_usd_mwh,
                target.ingestion_timestamp = source.ingestion_timestamp
        WHEN NOT MATCHED THEN
            INSERT (spp_id, settlement_point, interval_datetime, spp_usd_mwh,
                    congestion_price_usd_mwh, loss_price_usd_mwh, data_source, ingestion_timestamp)
            VALUES (source.spp_id, source.settlement_point, source.interval_datetime,
                    source.spp_usd_mwh, source.congestion_price_usd_mwh, source.loss_price_usd_mwh,
                    source.data_source, source.ingestion_timestamp)
        """

        await execute_sql(sql)
        return len(records)

    async def ingest_day_ahead_prices(
        self,
        settlement_point: str,
        delivery_date: Optional[datetime.date] = None
    ) -> Dict[str, Any]:
        """
        Ingest Day-Ahead Market (DAM) prices

        Args:
            settlement_point: Settlement point code
            delivery_date: Delivery date (default: tomorrow)

        Returns:
            Ingestion result
        """
        if delivery_date is None:
            delivery_date = (datetime.now() + timedelta(days=1)).date()

        log_id = str(uuid.uuid4())
        start_time = datetime.now()

        try:
            # Fetch DAM prices (15-minute intervals)
            raw_records = await self.client.get_day_ahead_prices(settlement_point, delivery_date)

            # Load into Delta table
            records_loaded = await self._load_day_ahead_prices(raw_records)

            # Log success
            duration = (datetime.now() - start_time).total_seconds()
            await self._log_ingestion(
                log_id, 'ERCOT', 'DAY_AHEAD_PRICES', delivery_date,
                settlement_point, records_loaded, 0, start_time, 'SUCCESS', duration
            )

            return {
                'status': 'SUCCESS',
                'records_loaded': records_loaded,
                'settlement_point': settlement_point,
                'delivery_date': delivery_date.isoformat(),
            }

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            await self._log_ingestion(
                log_id, 'ERCOT', 'DAY_AHEAD_PRICES', delivery_date,
                settlement_point, 0, 0, start_time, 'FAILED', duration, str(e)
            )
            raise

    async def _load_day_ahead_prices(self, records: List[Dict[str, Any]]) -> int:
        """Load day-ahead price records"""
        if not records:
            return 0

        values_list = []
        for record in records:
            dam_id = str(uuid.uuid4())
            values_list.append(f"""(
                '{dam_id}',
                '{record['settlement_point']}',
                DATE'{record['delivery_date']}',
                {record['delivery_hour']},
                {record['delivery_interval']},
                TIMESTAMP'{record['delivery_start']}',
                {record['lmp_usd_mwh']},
                {record['energy_price_usd_mwh']},
                {record['congestion_price_usd_mwh']},
                {record['loss_price_usd_mwh']},
                'ERCOT',
                CURRENT_TIMESTAMP()
            )""")

        values_str = ',\n'.join(values_list)

        sql = f"""
        MERGE INTO {self.catalog}.market_ercot.day_ahead_prices AS target
        USING (
            SELECT * FROM VALUES
            {values_str}
            AS tmp(dam_id, settlement_point, delivery_date, delivery_hour, delivery_interval,
                   delivery_start, lmp_usd_mwh, energy_price_usd_mwh, congestion_price_usd_mwh,
                   loss_price_usd_mwh, data_source, ingestion_timestamp)
        ) AS source
        ON target.settlement_point = source.settlement_point
           AND target.delivery_start = source.delivery_start
        WHEN MATCHED THEN
            UPDATE SET
                target.lmp_usd_mwh = source.lmp_usd_mwh,
                target.energy_price_usd_mwh = source.energy_price_usd_mwh,
                target.congestion_price_usd_mwh = source.congestion_price_usd_mwh,
                target.loss_price_usd_mwh = source.loss_price_usd_mwh,
                target.ingestion_timestamp = source.ingestion_timestamp
        WHEN NOT MATCHED THEN
            INSERT (dam_id, settlement_point, delivery_date, delivery_hour, delivery_interval,
                    delivery_start, lmp_usd_mwh, energy_price_usd_mwh, congestion_price_usd_mwh,
                    loss_price_usd_mwh, data_source, ingestion_timestamp)
            VALUES (source.dam_id, source.settlement_point, source.delivery_date,
                    source.delivery_hour, source.delivery_interval, source.delivery_start,
                    source.lmp_usd_mwh, source.energy_price_usd_mwh, source.congestion_price_usd_mwh,
                    source.loss_price_usd_mwh, source.data_source, source.ingestion_timestamp)
        """

        await execute_sql(sql)
        return len(records)

    async def ingest_load_forecast(
        self,
        forecast_type: str = 'SHORT_TERM'
    ) -> Dict[str, Any]:
        """
        Ingest system load forecast

        Args:
            forecast_type: 'SHORT_TERM', 'MID_TERM', or 'LONG_TERM'

        Returns:
            Ingestion result
        """
        log_id = str(uuid.uuid4())
        start_time = datetime.now()
        today = datetime.now()
        end_date = today + timedelta(days=7 if forecast_type == 'SHORT_TERM' else 30)

        try:
            # Fetch load forecast
            raw_records = await self.client.get_load_forecast(forecast_type, today, end_date)

            # Load into Delta table
            records_loaded = await self._load_load_forecasts(raw_records)

            # Log success
            duration = (datetime.now() - start_time).total_seconds()
            await self._log_ingestion(
                log_id, 'ERCOT', f'LOAD_FORECAST_{forecast_type}', today.date(),
                'SYSTEM', records_loaded, 0, start_time, 'SUCCESS', duration
            )

            return {'status': 'SUCCESS', 'records_loaded': records_loaded}

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            await self._log_ingestion(
                log_id, 'ERCOT', f'LOAD_FORECAST_{forecast_type}', today.date(),
                'SYSTEM', 0, 0, start_time, 'FAILED', duration, str(e)
            )
            raise

    async def _load_load_forecasts(self, records: List[Dict[str, Any]]) -> int:
        """Load load forecast records"""
        if not records:
            return 0

        values_list = []
        for record in records:
            forecast_id = str(uuid.uuid4())
            values_list.append(f"""(
                '{forecast_id}',
                '{record['forecast_type']}',
                TIMESTAMP'{record['forecast_timestamp']}',
                TIMESTAMP'{record['delivery_start']}',
                TIMESTAMP'{record['delivery_end']}',
                {record['forecasted_load_mw']},
                'ERCOT',
                CURRENT_TIMESTAMP()
            )""")

        values_str = ',\n'.join(values_list)

        sql = f"""
        MERGE INTO {self.catalog}.market_ercot.load_forecasts AS target
        USING (
            SELECT * FROM VALUES
            {values_str}
            AS tmp(forecast_id, forecast_type, forecast_timestamp, delivery_start,
                   delivery_end, forecasted_load_mw, forecast_source, ingestion_timestamp)
        ) AS source
        ON target.delivery_start = source.delivery_start
           AND target.forecast_type = source.forecast_type
        WHEN MATCHED THEN
            UPDATE SET
                target.forecasted_load_mw = source.forecasted_load_mw,
                target.forecast_timestamp = source.forecast_timestamp,
                target.ingestion_timestamp = source.ingestion_timestamp
        WHEN NOT MATCHED THEN
            INSERT (forecast_id, forecast_type, forecast_timestamp, delivery_start,
                    delivery_end, forecasted_load_mw, forecast_source, ingestion_timestamp)
            VALUES (source.forecast_id, source.forecast_type, source.forecast_timestamp,
                    source.delivery_start, source.delivery_end, source.forecasted_load_mw,
                    source.forecast_source, source.ingestion_timestamp)
        """

        await execute_sql(sql)
        return len(records)

    async def ingest_renewable_generation(
        self,
        fuel_type: str,
        date: Optional[datetime.date] = None
    ) -> Dict[str, Any]:
        """
        Ingest actual renewable generation (wind/solar)

        Args:
            fuel_type: 'WIND' or 'SOLAR'
            date: Date to fetch (default: today)

        Returns:
            Ingestion result
        """
        if date is None:
            date = datetime.now().date()

        log_id = str(uuid.uuid4())
        start_time = datetime.now()

        try:
            # Fetch renewable generation
            raw_records = await self.client.get_renewable_generation(fuel_type, date)

            # Load into Delta table
            records_loaded = await self._load_renewable_generation(raw_records)

            # Log success
            duration = (datetime.now() - start_time).total_seconds()
            await self._log_ingestion(
                log_id, 'ERCOT', f'{fuel_type}_GENERATION', date,
                'SYSTEM', records_loaded, 0, start_time, 'SUCCESS', duration
            )

            return {'status': 'SUCCESS', 'records_loaded': records_loaded, 'fuel_type': fuel_type}

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            await self._log_ingestion(
                log_id, 'ERCOT', f'{fuel_type}_GENERATION', date,
                'SYSTEM', 0, 0, start_time, 'FAILED', duration, str(e)
            )
            raise

    async def _load_renewable_generation(self, records: List[Dict[str, Any]]) -> int:
        """Load renewable generation records"""
        if not records:
            return 0

        values_list = []
        for record in records:
            generation_id = str(uuid.uuid4())
            values_list.append(f"""(
                '{generation_id}',
                TIMESTAMP'{record['timestamp']}',
                '{record['fuel_type']}',
                {record['actual_generation_mw']},
                {record['installed_capacity_mw']},
                {record['capacity_factor']},
                'ERCOT',
                CURRENT_TIMESTAMP()
            )""")

        values_str = ',\n'.join(values_list)

        sql = f"""
        MERGE INTO {self.catalog}.market_ercot.renewable_generation AS target
        USING (
            SELECT * FROM VALUES
            {values_str}
            AS tmp(generation_id, timestamp, fuel_type, actual_generation_mw,
                   installed_capacity_mw, capacity_factor, data_source, ingestion_timestamp)
        ) AS source
        ON target.timestamp = source.timestamp
           AND target.fuel_type = source.fuel_type
        WHEN MATCHED THEN
            UPDATE SET
                target.actual_generation_mw = source.actual_generation_mw,
                target.installed_capacity_mw = source.installed_capacity_mw,
                target.capacity_factor = source.capacity_factor,
                target.ingestion_timestamp = source.ingestion_timestamp
        WHEN NOT MATCHED THEN
            INSERT (generation_id, timestamp, fuel_type, actual_generation_mw,
                    installed_capacity_mw, capacity_factor, data_source, ingestion_timestamp)
            VALUES (source.generation_id, source.timestamp, source.fuel_type,
                    source.actual_generation_mw, source.installed_capacity_mw,
                    source.capacity_factor, source.data_source, source.ingestion_timestamp)
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
_ercot_service: Optional[ERCOTIngestionService] = None


def get_ercot_ingestion_service() -> ERCOTIngestionService:
    """Get ERCOT ingestion service singleton"""
    global _ercot_service
    if _ercot_service is None:
        # API key should come from config/environment
        api_key = get_settings().ercot_api_key if hasattr(get_settings(), 'ercot_api_key') else None
        _ercot_service = ERCOTIngestionService(api_key)
    return _ercot_service
