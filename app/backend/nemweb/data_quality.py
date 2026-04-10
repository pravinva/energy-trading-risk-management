"""
Data Quality Validation for NEMWEB Ingestion
Checks completeness, timeliness, accuracy, and consistency
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from app.backend.config import get_settings
from app.backend.database import execute_sql


class DataQualityValidator:
    """
    Data quality validator for NEMWEB data

    Metrics:
    - Completeness: All expected intervals present?
    - Timeliness: Data arriving within SLA?
    - Accuracy: Values within expected ranges?
    - Consistency: Related tables aligned?
    """

    def __init__(self):
        """Initialize validator"""
        self.catalog = get_settings().apex_catalog

    async def run_all_checks(
        self,
        date: Optional[datetime] = None,
        region_id: str = 'NSW1',
    ) -> List[Dict[str, Any]]:
        """
        Run all data quality checks

        Args:
            date: Date to check (default: today)
            region_id: Region to check

        Returns:
            List of check results
        """
        if date is None:
            date = datetime.now()

        results = []

        # Completeness checks
        results.append(await self.check_completeness_dispatch_prices(date, region_id))
        results.append(await self.check_completeness_predispatch(date, region_id))

        # Timeliness checks
        results.append(await self.check_timeliness_dispatch(region_id))

        # Accuracy checks
        results.append(await self.check_price_ranges(date, region_id))
        results.append(await self.check_demand_ranges(date, region_id))

        # Consistency checks
        results.append(await self.check_price_demand_consistency(date, region_id))

        return results

    async def check_completeness_dispatch_prices(
        self,
        date: datetime,
        region_id: str,
    ) -> Dict[str, Any]:
        """
        Check completeness of dispatch prices

        5-minute intervals = 288 intervals per day (12 per hour * 24 hours)

        Args:
            date: Date to check
            region_id: Region to check

        Returns:
            Check result with pass/fail
        """
        metric_id = str(uuid.uuid4())
        check_timestamp = datetime.now()

        try:
            # Count intervals for the date
            sql = f"""
            SELECT COUNT(*) AS interval_count
            FROM {self.catalog}.market_nem.dispatch_prices
            WHERE DATE(interval_datetime) = DATE'{date.date()}'
              AND region_id = '{region_id}'
              AND data_source = 'NEMWEB'
            """

            rows = await execute_sql(sql)
            interval_count = int(rows[0].get('interval_count', 0)) if rows else 0

            # Expected: 288 intervals (5-minute intervals for 24 hours)
            expected_intervals = 288
            completeness_pct = (interval_count / expected_intervals) * 100

            # Pass if > 95% complete
            threshold = 95.0
            passed = completeness_pct >= threshold

            details = f"Found {interval_count}/{expected_intervals} intervals ({completeness_pct:.1f}%)"

            # Log result
            await self._log_quality_metric(
                metric_id=metric_id,
                check_timestamp=check_timestamp,
                data_type='DISPATCH_PRICES',
                region_id=region_id,
                date_checked=date.date(),
                metric_name='COMPLETENESS',
                metric_value=completeness_pct,
                threshold_value=threshold,
                passed=passed,
                details=details,
            )

            return {
                'metric': 'COMPLETENESS_DISPATCH_PRICES',
                'value': completeness_pct,
                'threshold': threshold,
                'passed': passed,
                'details': details,
            }

        except Exception as e:
            print(f"Error checking completeness: {e}")
            return {
                'metric': 'COMPLETENESS_DISPATCH_PRICES',
                'passed': False,
                'error': str(e),
            }

    async def check_completeness_predispatch(
        self,
        date: datetime,
        region_id: str,
    ) -> Dict[str, Any]:
        """
        Check completeness of pre-dispatch forecasts

        Pre-dispatch runs every 30 minutes, forecasts up to 40 hours ahead

        Args:
            date: Date to check
            region_id: Region to check

        Returns:
            Check result
        """
        metric_id = str(uuid.uuid4())
        check_timestamp = datetime.now()

        try:
            sql = f"""
            SELECT COUNT(*) AS forecast_count
            FROM {self.catalog}.market_nem.predispatch_forecasts
            WHERE DATE(predispatch_run_datetime) = DATE'{date.date()}'
              AND region_id = '{region_id}'
            """

            rows = await execute_sql(sql)
            forecast_count = int(rows[0].get('forecast_count', 0)) if rows else 0

            # Expected: roughly 48 runs * 480 intervals = 23,040 forecasts per day
            # (But this varies, so we use a lower threshold)
            min_expected = 10000
            completeness_pct = (forecast_count / min_expected) * 100

            threshold = 50.0  # More lenient for forecasts
            passed = completeness_pct >= threshold

            details = f"Found {forecast_count} forecast intervals"

            await self._log_quality_metric(
                metric_id=metric_id,
                check_timestamp=check_timestamp,
                data_type='PREDISPATCH_FORECASTS',
                region_id=region_id,
                date_checked=date.date(),
                metric_name='COMPLETENESS',
                metric_value=completeness_pct,
                threshold_value=threshold,
                passed=passed,
                details=details,
            )

            return {
                'metric': 'COMPLETENESS_PREDISPATCH',
                'value': forecast_count,
                'threshold': min_expected,
                'passed': passed,
                'details': details,
            }

        except Exception as e:
            print(f"Error checking predispatch completeness: {e}")
            return {'metric': 'COMPLETENESS_PREDISPATCH', 'passed': False, 'error': str(e)}

    async def check_timeliness_dispatch(self, region_id: str) -> Dict[str, Any]:
        """
        Check timeliness of dispatch price data

        Data should be available within 10 minutes of interval end

        Args:
            region_id: Region to check

        Returns:
            Check result
        """
        metric_id = str(uuid.uuid4())
        check_timestamp = datetime.now()

        try:
            # Get latest data timestamp
            sql = f"""
            SELECT
                MAX(interval_datetime) AS latest_data_timestamp,
                MAX(ingestion_timestamp) AS latest_ingestion_timestamp
            FROM {self.catalog}.market_nem.dispatch_prices
            WHERE region_id = '{region_id}'
              AND data_source = 'NEMWEB'
            """

            rows = await execute_sql(sql)

            if not rows or not rows[0].get('latest_data_timestamp'):
                return {'metric': 'TIMELINESS_DISPATCH', 'passed': False, 'error': 'No data found'}

            latest_data_ts = rows[0].get('latest_data_timestamp')
            latest_ingestion_ts = rows[0].get('latest_ingestion_timestamp')

            # Calculate lag (minutes between interval and now)
            minutes_lag = (datetime.now() - latest_data_ts).total_seconds() / 60

            # Threshold: data should be < 30 minutes old
            threshold = 30.0
            passed = minutes_lag < threshold

            details = f"Latest data: {latest_data_ts}, Lag: {minutes_lag:.1f} minutes"

            await self._log_quality_metric(
                metric_id=metric_id,
                check_timestamp=check_timestamp,
                data_type='DISPATCH_PRICES',
                region_id=region_id,
                date_checked=datetime.now().date(),
                metric_name='TIMELINESS',
                metric_value=minutes_lag,
                threshold_value=threshold,
                passed=passed,
                details=details,
            )

            return {
                'metric': 'TIMELINESS_DISPATCH',
                'value': minutes_lag,
                'threshold': threshold,
                'passed': passed,
                'details': details,
            }

        except Exception as e:
            print(f"Error checking timeliness: {e}")
            return {'metric': 'TIMELINESS_DISPATCH', 'passed': False, 'error': str(e)}

    async def check_price_ranges(
        self,
        date: datetime,
        region_id: str,
    ) -> Dict[str, Any]:
        """
        Check if prices are within expected ranges

        NEM prices typically range from -$1,000 to $16,600/MWh
        (market price cap)

        Args:
            date: Date to check
            region_id: Region to check

        Returns:
            Check result
        """
        metric_id = str(uuid.uuid4())
        check_timestamp = datetime.now()

        try:
            sql = f"""
            SELECT
                MIN(rrp) AS min_price,
                MAX(rrp) AS max_price,
                AVG(rrp) AS avg_price,
                COUNT(*) AS total_intervals,
                SUM(CASE WHEN rrp < -1000 OR rrp > 16600 THEN 1 ELSE 0 END) AS out_of_range_count
            FROM {self.catalog}.market_nem.dispatch_prices
            WHERE DATE(interval_datetime) = DATE'{date.date()}'
              AND region_id = '{region_id}'
              AND data_source = 'NEMWEB'
            """

            rows = await execute_sql(sql)

            if not rows:
                return {'metric': 'ACCURACY_PRICE_RANGES', 'passed': False, 'error': 'No data'}

            result = rows[0]
            out_of_range = int(result.get('out_of_range_count', 0))
            total = int(result.get('total_intervals', 1))

            accuracy_pct = ((total - out_of_range) / total) * 100

            threshold = 99.0  # 99% of prices should be in range
            passed = accuracy_pct >= threshold

            details = f"Min: ${result.get('min_price'):.2f}, Max: ${result.get('max_price'):.2f}, Avg: ${result.get('avg_price'):.2f}, Out of range: {out_of_range}/{total}"

            await self._log_quality_metric(
                metric_id=metric_id,
                check_timestamp=check_timestamp,
                data_type='DISPATCH_PRICES',
                region_id=region_id,
                date_checked=date.date(),
                metric_name='ACCURACY',
                metric_value=accuracy_pct,
                threshold_value=threshold,
                passed=passed,
                details=details,
            )

            return {
                'metric': 'ACCURACY_PRICE_RANGES',
                'value': accuracy_pct,
                'threshold': threshold,
                'passed': passed,
                'details': details,
            }

        except Exception as e:
            print(f"Error checking price ranges: {e}")
            return {'metric': 'ACCURACY_PRICE_RANGES', 'passed': False, 'error': str(e)}

    async def check_demand_ranges(
        self,
        date: datetime,
        region_id: str,
    ) -> Dict[str, Any]:
        """
        Check if demand values are within expected ranges

        NSW demand typically ranges from 5,000 to 15,000 MW

        Args:
            date: Date to check
            region_id: Region to check

        Returns:
            Check result
        """
        metric_id = str(uuid.uuid4())
        check_timestamp = datetime.now()

        try:
            # Region-specific demand ranges (MW)
            demand_ranges = {
                'NSW1': (4000, 16000),
                'VIC1': (3000, 10000),
                'QLD1': (4000, 10000),
                'SA1': (500, 4000),
                'TAS1': (500, 2000),
            }

            min_demand, max_demand = demand_ranges.get(region_id, (0, 20000))

            sql = f"""
            SELECT
                MIN(demand_mw) AS min_demand,
                MAX(demand_mw) AS max_demand,
                AVG(demand_mw) AS avg_demand,
                COUNT(*) AS total_intervals,
                SUM(CASE WHEN demand_mw < {min_demand} OR demand_mw > {max_demand} THEN 1 ELSE 0 END) AS out_of_range_count
            FROM {self.catalog}.market_nem.dispatch_prices
            WHERE DATE(interval_datetime) = DATE'{date.date()}'
              AND region_id = '{region_id}'
              AND data_source = 'NEMWEB'
            """

            rows = await execute_sql(sql)

            if not rows:
                return {'metric': 'ACCURACY_DEMAND_RANGES', 'passed': False, 'error': 'No data'}

            result = rows[0]
            out_of_range = int(result.get('out_of_range_count', 0))
            total = int(result.get('total_intervals', 1))

            accuracy_pct = ((total - out_of_range) / total) * 100

            threshold = 95.0
            passed = accuracy_pct >= threshold

            details = f"Min: {result.get('min_demand'):.0f} MW, Max: {result.get('max_demand'):.0f} MW, Avg: {result.get('avg_demand'):.0f} MW, Expected range: {min_demand}-{max_demand} MW"

            await self._log_quality_metric(
                metric_id=metric_id,
                check_timestamp=check_timestamp,
                data_type='DISPATCH_PRICES',
                region_id=region_id,
                date_checked=date.date(),
                metric_name='ACCURACY',
                metric_value=accuracy_pct,
                threshold_value=threshold,
                passed=passed,
                details=details,
            )

            return {
                'metric': 'ACCURACY_DEMAND_RANGES',
                'value': accuracy_pct,
                'threshold': threshold,
                'passed': passed,
                'details': details,
            }

        except Exception as e:
            print(f"Error checking demand ranges: {e}")
            return {'metric': 'ACCURACY_DEMAND_RANGES', 'passed': False, 'error': str(e)}

    async def check_price_demand_consistency(
        self,
        date: datetime,
        region_id: str,
    ) -> Dict[str, Any]:
        """
        Check consistency between price and demand tables

        Should have matching intervals

        Args:
            date: Date to check
            region_id: Region to check

        Returns:
            Check result
        """
        metric_id = str(uuid.uuid4())
        check_timestamp = datetime.now()

        try:
            # Count intervals in each table
            sql_prices = f"""
            SELECT COUNT(*) AS count
            FROM {self.catalog}.market_nem.dispatch_prices
            WHERE DATE(interval_datetime) = DATE'{date.date()}'
              AND region_id = '{region_id}'
            """

            sql_demand = f"""
            SELECT COUNT(*) AS count
            FROM {self.catalog}.market_nem.demand_actual
            WHERE DATE(interval_datetime) = DATE'{date.date()}'
              AND region_id = '{region_id}'
            """

            price_rows = await execute_sql(sql_prices)
            demand_rows = await execute_sql(sql_demand)

            price_count = int(price_rows[0].get('count', 0)) if price_rows else 0
            demand_count = int(demand_rows[0].get('count', 0)) if demand_rows else 0

            # Calculate consistency (should be close to 100%)
            if price_count == 0 and demand_count == 0:
                consistency_pct = 100.0
            elif price_count == 0 or demand_count == 0:
                consistency_pct = 0.0
            else:
                consistency_pct = (min(price_count, demand_count) / max(price_count, demand_count)) * 100

            threshold = 90.0
            passed = consistency_pct >= threshold

            details = f"Prices: {price_count} intervals, Demand: {demand_count} intervals, Consistency: {consistency_pct:.1f}%"

            await self._log_quality_metric(
                metric_id=metric_id,
                check_timestamp=check_timestamp,
                data_type='CONSISTENCY_CHECK',
                region_id=region_id,
                date_checked=date.date(),
                metric_name='CONSISTENCY',
                metric_value=consistency_pct,
                threshold_value=threshold,
                passed=passed,
                details=details,
            )

            return {
                'metric': 'CONSISTENCY_PRICE_DEMAND',
                'value': consistency_pct,
                'threshold': threshold,
                'passed': passed,
                'details': details,
            }

        except Exception as e:
            print(f"Error checking consistency: {e}")
            return {'metric': 'CONSISTENCY_PRICE_DEMAND', 'passed': False, 'error': str(e)}

    async def _log_quality_metric(
        self,
        metric_id: str,
        check_timestamp: datetime,
        data_type: str,
        region_id: str,
        date_checked: Any,
        metric_name: str,
        metric_value: float,
        threshold_value: float,
        passed: bool,
        details: str,
    ):
        """Log quality metric to database"""
        try:
            sql = f"""
            INSERT INTO {self.catalog}.nemweb.data_quality_metrics
            (metric_id, check_timestamp, data_type, region_id, date_checked,
             metric_name, metric_value, threshold_value, passed, details)
            VALUES (
                '{metric_id}',
                TIMESTAMP'{check_timestamp}',
                '{data_type}',
                '{region_id}',
                DATE'{date_checked}',
                '{metric_name}',
                {metric_value},
                {threshold_value},
                {str(passed).lower()},
                '{details.replace("'", "''")}'
            )
            """
            await execute_sql(sql)
        except Exception as e:
            print(f"Error logging quality metric: {e}")


# Singleton instance
_validator: Optional[DataQualityValidator] = None


def get_quality_validator() -> DataQualityValidator:
    """Get quality validator singleton"""
    global _validator
    if _validator is None:
        _validator = DataQualityValidator()
    return _validator
