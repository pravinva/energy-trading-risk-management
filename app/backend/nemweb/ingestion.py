"""
NEMWEB Data Ingestion Service
Fetches data from NEMWEB and loads into Delta tables
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from app.backend.config import get_settings
from app.backend.database import execute_sql
from app.backend.nemweb.client import get_nemweb_client, NEMWEBClient


class NEMWEBIngestionService:
    """
    Service for ingesting NEMWEB data into Delta tables

    Features:
    - Real-time dispatch price ingestion
    - Pre-dispatch forecast ingestion
    - Demand actuals ingestion
    - Historical data backfill
    - Data quality validation
    - Ingestion logging
    """

    def __init__(self):
        """Initialize ingestion service"""
        self.catalog = get_settings().apex_catalog
        self.client: Optional[NEMWEBClient] = None

    async def ingest_dispatch_prices(
        self,
        date: Optional[datetime] = None,
        regions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Ingest 5-minute dispatch prices for a date

        Args:
            date: Date to ingest (default: today)
            regions: Regions to ingest (default: all NEM regions)

        Returns:
            Ingestion result with status and counts
        """
        if date is None:
            date = datetime.now()

        if regions is None:
            regions = ['NSW1', 'VIC1', 'QLD1', 'SA1', 'TAS1']

        log_id = str(uuid.uuid4())
        start_time = datetime.now()

        try:
            # Get NEMWEB client
            if self.client is None:
                self.client = await get_nemweb_client()

            # Fetch data from NEMWEB
            print(f"Fetching dispatch prices for {date.date()} from NEMWEB...")
            raw_records = await self.client.get_dispatch_prices(date, regions)

            if not raw_records:
                print(f"No dispatch price data available for {date.date()}")
                await self._log_ingestion(
                    log_id=log_id,
                    data_type='DISPATCH_PRICES',
                    date_loaded=date.date(),
                    region_id='ALL',
                    records_loaded=0,
                    records_failed=0,
                    start_timestamp=start_time,
                    status='SUCCESS',
                    error_message='No data available from NEMWEB',
                )
                return {
                    'status': 'SUCCESS',
                    'records_loaded': 0,
                    'message': 'No data available',
                }

            # Transform records
            transformed = self._transform_dispatch_prices(raw_records)

            # Load into Delta table
            records_loaded = await self._load_dispatch_prices(transformed)

            # Log success
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            await self._log_ingestion(
                log_id=log_id,
                data_type='DISPATCH_PRICES',
                date_loaded=date.date(),
                region_id='ALL',
                records_loaded=records_loaded,
                records_failed=0,
                start_timestamp=start_time,
                end_timestamp=end_time,
                duration_seconds=duration,
                status='SUCCESS',
            )

            print(f"Successfully loaded {records_loaded} dispatch price records")

            return {
                'status': 'SUCCESS',
                'records_loaded': records_loaded,
                'duration_seconds': duration,
            }

        except Exception as e:
            # Log failure
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            await self._log_ingestion(
                log_id=log_id,
                data_type='DISPATCH_PRICES',
                date_loaded=date.date(),
                region_id='ALL',
                records_loaded=0,
                records_failed=0,
                start_timestamp=start_time,
                end_timestamp=end_time,
                duration_seconds=duration,
                status='FAILED',
                error_message=str(e),
            )

            print(f"Error ingesting dispatch prices: {e}")

            return {
                'status': 'FAILED',
                'error': str(e),
            }

    async def ingest_predispatch_forecasts(
        self,
        region_id: str = 'NSW1',
        hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Ingest pre-dispatch forecasts

        Args:
            region_id: Region to ingest
            hours: Forecast horizon in hours

        Returns:
            Ingestion result
        """
        log_id = str(uuid.uuid4())
        start_time = datetime.now()

        try:
            if self.client is None:
                self.client = await get_nemweb_client()

            print(f"Fetching pre-dispatch forecasts for {region_id}...")
            raw_records = await self.client.get_predispatch_forecast(region_id, hours)

            if not raw_records:
                print(f"No pre-dispatch data available for {region_id}")
                return {'status': 'SUCCESS', 'records_loaded': 0}

            # Transform and load
            transformed = self._transform_predispatch(raw_records, region_id)
            records_loaded = await self._load_predispatch(transformed)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            await self._log_ingestion(
                log_id=log_id,
                data_type='PREDISPATCH_FORECASTS',
                date_loaded=datetime.now().date(),
                region_id=region_id,
                records_loaded=records_loaded,
                records_failed=0,
                start_timestamp=start_time,
                end_timestamp=end_time,
                duration_seconds=duration,
                status='SUCCESS',
            )

            print(f"Successfully loaded {records_loaded} pre-dispatch records")

            return {
                'status': 'SUCCESS',
                'records_loaded': records_loaded,
                'duration_seconds': duration,
            }

        except Exception as e:
            print(f"Error ingesting pre-dispatch: {e}")
            return {'status': 'FAILED', 'error': str(e)}

    async def ingest_demand_actual(
        self,
        region_id: str = 'NSW1',
        date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Ingest actual demand data

        Args:
            region_id: Region to ingest
            date: Date to ingest

        Returns:
            Ingestion result
        """
        if date is None:
            date = datetime.now()

        log_id = str(uuid.uuid4())
        start_time = datetime.now()

        try:
            if self.client is None:
                self.client = await get_nemweb_client()

            print(f"Fetching demand actual for {region_id} on {date.date()}...")
            raw_records = await self.client.get_demand_actual(region_id, date)

            if not raw_records:
                print(f"No demand data available")
                return {'status': 'SUCCESS', 'records_loaded': 0}

            # Transform and load
            transformed = self._transform_demand(raw_records, region_id)
            records_loaded = await self._load_demand(transformed)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            await self._log_ingestion(
                log_id=log_id,
                data_type='DEMAND_ACTUAL',
                date_loaded=date.date(),
                region_id=region_id,
                records_loaded=records_loaded,
                records_failed=0,
                start_timestamp=start_time,
                end_timestamp=end_time,
                duration_seconds=duration,
                status='SUCCESS',
            )

            print(f"Successfully loaded {records_loaded} demand records")

            return {
                'status': 'SUCCESS',
                'records_loaded': records_loaded,
                'duration_seconds': duration,
            }

        except Exception as e:
            print(f"Error ingesting demand actual: {e}")
            return {'status': 'FAILED', 'error': str(e)}

    async def backfill_historical_prices(
        self,
        start_date: datetime,
        end_date: datetime,
        region_id: str = 'NSW1',
    ) -> Dict[str, Any]:
        """
        Backfill historical dispatch prices for date range

        Args:
            start_date: Start date
            end_date: End date
            region_id: Region to backfill

        Returns:
            Backfill result with total records loaded
        """
        print(f"\n{'='*60}")
        print(f"HISTORICAL BACKFILL: {region_id}")
        print(f"Period: {start_date.date()} to {end_date.date()}")
        print(f"{'='*60}\n")

        total_records = 0
        total_days = (end_date - start_date).days + 1

        try:
            if self.client is None:
                self.client = await get_nemweb_client()

            # Fetch all historical data
            raw_records = await self.client.get_historical_prices(
                start_date, end_date, region_id
            )

            if not raw_records:
                print("No historical data available")
                return {'status': 'SUCCESS', 'records_loaded': 0}

            # Transform and load in batches (by day)
            records_by_day: Dict[str, List[Dict]] = {}

            for record in raw_records:
                interval_dt = self._parse_datetime(record.get('SETTLEMENTDATE', ''))
                day_key = interval_dt.date().isoformat()

                if day_key not in records_by_day:
                    records_by_day[day_key] = []

                records_by_day[day_key].append(record)

            # Load each day
            for day_key, day_records in records_by_day.items():
                transformed = self._transform_dispatch_prices(day_records)
                loaded = await self._load_dispatch_prices(transformed)
                total_records += loaded

                print(f"Loaded {loaded} records for {day_key}")

            print(f"\nBackfill complete: {total_records} total records loaded")

            return {
                'status': 'SUCCESS',
                'records_loaded': total_records,
                'days_processed': len(records_by_day),
                'total_days': total_days,
            }

        except Exception as e:
            print(f"Error in historical backfill: {e}")
            return {'status': 'FAILED', 'error': str(e)}

    def _transform_dispatch_prices(
        self, raw_records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform raw NEMWEB dispatch price records"""
        transformed = []

        for record in raw_records:
            try:
                transformed.append({
                    'dispatch_id': str(uuid.uuid4()),
                    'interval_datetime': self._parse_datetime(record.get('SETTLEMENTDATE', '')),
                    'region_id': record.get('REGIONID', ''),
                    'rrp': float(record.get('RRP', 0)),
                    'rop': float(record.get('ROP', 0)),
                    'demand_mw': float(record.get('TOTALDEMAND', 0)),
                    'intervention': int(record.get('INTERVENTION', '0')),
                    'raise_6sec_price': float(record.get('RAISE6SECRRP', 0)),
                    'raise_60sec_price': float(record.get('RAISE60SECRRP', 0)),
                    'raise_5min_price': float(record.get('RAISE5MINRRP', 0)),
                    'raise_reg_price': float(record.get('RAISEREGRRP', 0)),
                    'lower_6sec_price': float(record.get('LOWER6SECRRP', 0)),
                    'lower_60sec_price': float(record.get('LOWER60SECRRP', 0)),
                    'lower_5min_price': float(record.get('LOWER5MINRRP', 0)),
                    'lower_reg_price': float(record.get('LOWERREGRRP', 0)),
                    'ingestion_timestamp': datetime.now(),
                    'data_source': 'NEMWEB',
                })
            except Exception as e:
                print(f"Error transforming dispatch record: {e}")
                continue

        return transformed

    def _transform_predispatch(
        self, raw_records: List[Dict[str, Any]], region_id: str
    ) -> List[Dict[str, Any]]:
        """Transform raw pre-dispatch forecast records"""
        transformed = []

        for record in raw_records:
            try:
                predispatch_time = self._parse_datetime(record.get('PREDISPATCH_RUN_DATETIME', ''))
                interval_time = self._parse_datetime(record.get('DATETIME', ''))

                forecast_horizon_minutes = int((interval_time - predispatch_time).total_seconds() / 60)

                transformed.append({
                    'forecast_id': str(uuid.uuid4()),
                    'predispatch_run_datetime': predispatch_time,
                    'interval_datetime': interval_time,
                    'region_id': region_id,
                    'forecast_price': float(record.get('RRP', 0)),
                    'forecast_demand_mw': float(record.get('DEMAND', 0)),
                    'forecast_horizon_minutes': forecast_horizon_minutes,
                    'intervention': int(record.get('INTERVENTION', '0')),
                    'ingestion_timestamp': datetime.now(),
                })
            except Exception as e:
                print(f"Error transforming predispatch record: {e}")
                continue

        return transformed

    def _transform_demand(
        self, raw_records: List[Dict[str, Any]], region_id: str
    ) -> List[Dict[str, Any]]:
        """Transform raw demand actual records"""
        transformed = []

        for record in raw_records:
            try:
                transformed.append({
                    'demand_id': str(uuid.uuid4()),
                    'interval_datetime': self._parse_datetime(record.get('SETTLEMENTDATE', '')),
                    'region_id': region_id,
                    'total_demand_mw': float(record.get('TOTALDEMAND', 0)),
                    'operational_demand_mw': float(record.get('OPERATIONAL_DEMAND', 0)),
                    'available_generation_mw': float(record.get('AVAILABLEGENERATION', 0)),
                    'available_load_mw': float(record.get('AVAILABLELOAD', 0)),
                    'semi_scheduled_generation_mw': float(record.get('SEMISCHEDULEDGENERATION', 0)),
                    'rooftop_solar_mw': float(record.get('ROOFTOP_SOLAR', 0)),
                    'ingestion_timestamp': datetime.now(),
                })
            except Exception as e:
                print(f"Error transforming demand record: {e}")
                continue

        return transformed

    async def _load_dispatch_prices(self, records: List[Dict[str, Any]]) -> int:
        """Load dispatch price records into Delta table"""
        if not records:
            return 0

        # Use MERGE to handle duplicates (upsert based on interval_datetime + region_id)
        for record in records:
            try:
                sql = f"""
                MERGE INTO {self.catalog}.market_nem.dispatch_prices AS target
                USING (
                    SELECT
                        '{record['dispatch_id']}' AS dispatch_id,
                        TIMESTAMP'{record['interval_datetime']}' AS interval_datetime,
                        '{record['region_id']}' AS region_id,
                        {record['rrp']} AS rrp,
                        {record['rop']} AS rop,
                        {record['demand_mw']} AS demand_mw,
                        {record['intervention']} AS intervention,
                        {record['raise_6sec_price']} AS raise_6sec_price,
                        {record['raise_60sec_price']} AS raise_60sec_price,
                        {record['raise_5min_price']} AS raise_5min_price,
                        {record['raise_reg_price']} AS raise_reg_price,
                        {record['lower_6sec_price']} AS lower_6sec_price,
                        {record['lower_60sec_price']} AS lower_60sec_price,
                        {record['lower_5min_price']} AS lower_5min_price,
                        {record['lower_reg_price']} AS lower_reg_price,
                        TIMESTAMP'{record['ingestion_timestamp']}' AS ingestion_timestamp,
                        '{record['data_source']}' AS data_source
                ) AS source
                ON target.interval_datetime = source.interval_datetime
                   AND target.region_id = source.region_id
                WHEN MATCHED THEN
                    UPDATE SET *
                WHEN NOT MATCHED THEN
                    INSERT *
                """
                await execute_sql(sql)
            except Exception as e:
                print(f"Error loading dispatch price record: {e}")
                continue

        return len(records)

    async def _load_predispatch(self, records: List[Dict[str, Any]]) -> int:
        """Load pre-dispatch forecast records"""
        if not records:
            return 0

        for record in records:
            try:
                sql = f"""
                INSERT INTO {self.catalog}.market_nem.predispatch_forecasts
                (forecast_id, predispatch_run_datetime, interval_datetime, region_id,
                 forecast_price, forecast_demand_mw, forecast_horizon_minutes,
                 intervention, ingestion_timestamp)
                VALUES (
                    '{record['forecast_id']}',
                    TIMESTAMP'{record['predispatch_run_datetime']}',
                    TIMESTAMP'{record['interval_datetime']}',
                    '{record['region_id']}',
                    {record['forecast_price']},
                    {record['forecast_demand_mw']},
                    {record['forecast_horizon_minutes']},
                    {record['intervention']},
                    TIMESTAMP'{record['ingestion_timestamp']}'
                )
                """
                await execute_sql(sql)
            except Exception as e:
                print(f"Error loading predispatch record: {e}")
                continue

        return len(records)

    async def _load_demand(self, records: List[Dict[str, Any]]) -> int:
        """Load demand actual records"""
        if not records:
            return 0

        for record in records:
            try:
                sql = f"""
                INSERT INTO {self.catalog}.market_nem.demand_actual
                (demand_id, interval_datetime, region_id, total_demand_mw,
                 operational_demand_mw, available_generation_mw, available_load_mw,
                 semi_scheduled_generation_mw, rooftop_solar_mw, ingestion_timestamp)
                VALUES (
                    '{record['demand_id']}',
                    TIMESTAMP'{record['interval_datetime']}',
                    '{record['region_id']}',
                    {record['total_demand_mw']},
                    {record['operational_demand_mw']},
                    {record['available_generation_mw']},
                    {record['available_load_mw']},
                    {record['semi_scheduled_generation_mw']},
                    {record['rooftop_solar_mw']},
                    TIMESTAMP'{record['ingestion_timestamp']}'
                )
                """
                await execute_sql(sql)
            except Exception as e:
                print(f"Error loading demand record: {e}")
                continue

        return len(records)

    async def _log_ingestion(
        self,
        log_id: str,
        data_type: str,
        date_loaded: Any,
        region_id: str,
        records_loaded: int,
        records_failed: int,
        start_timestamp: datetime,
        end_timestamp: Optional[datetime] = None,
        duration_seconds: Optional[float] = None,
        status: str = 'SUCCESS',
        error_message: Optional[str] = None,
    ):
        """Log ingestion job to database"""
        try:
            sql = f"""
            INSERT INTO {self.catalog}.nemweb.ingestion_log
            (log_id, data_type, date_loaded, region_id, records_loaded, records_failed,
             start_timestamp, end_timestamp, duration_seconds, status, error_message)
            VALUES (
                '{log_id}',
                '{data_type}',
                DATE'{date_loaded}',
                '{region_id}',
                {records_loaded},
                {records_failed},
                TIMESTAMP'{start_timestamp}',
                {'TIMESTAMP\'' + str(end_timestamp) + '\'' if end_timestamp else 'NULL'},
                {duration_seconds if duration_seconds else 'NULL'},
                '{status}',
                {'\'' + error_message.replace("'", "''") + '\'' if error_message else 'NULL'}
            )
            """
            await execute_sql(sql)
        except Exception as e:
            print(f"Error logging ingestion: {e}")

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


# Singleton instance
_service: Optional[NEMWEBIngestionService] = None


def get_ingestion_service() -> NEMWEBIngestionService:
    """Get ingestion service singleton"""
    global _service
    if _service is None:
        _service = NEMWEBIngestionService()
    return _service
