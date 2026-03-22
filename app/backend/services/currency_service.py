"""
Currency Conversion Service
For display purposes only - actual trading happens in native market currency
"""
from __future__ import annotations

from datetime import datetime, date
from typing import Dict, Optional
import uuid

from app.backend.database import execute_sql
from app.backend.config import get_settings


class CurrencyService:
    """
    Service for currency conversion (display purposes only)

    Markets trade in native currencies:
    - NEM: AUD
    - EPEX: EUR
    - ERCOT: USD

    This service allows viewing prices in different currencies for reference.
    """

    # Cache for exchange rates (refreshed periodically)
    _rate_cache: Dict[str, float] = {}
    _cache_timestamp: Optional[datetime] = None
    CACHE_DURATION_MINUTES = 60  # Refresh every hour

    @classmethod
    async def get_exchange_rate(cls, from_currency: str, to_currency: str) -> float:
        """
        Get exchange rate from one currency to another

        Args:
            from_currency: Source currency code ('AUD', 'EUR', 'USD')
            to_currency: Target currency code

        Returns:
            Exchange rate (multiply source amount by this to get target amount)
        """
        # Same currency = 1.0
        if from_currency == to_currency:
            return 1.0

        # Check cache
        cache_key = f"{from_currency}_{to_currency}"
        if cls._is_cache_valid() and cache_key in cls._rate_cache:
            return cls._rate_cache[cache_key]

        # Fetch from database
        catalog = get_settings().apex_catalog

        sql = f"""
        SELECT rate
        FROM {catalog}.core.latest_exchange_rates
        WHERE from_currency = '{from_currency}'
          AND to_currency = '{to_currency}'
        LIMIT 1
        """

        rows = await execute_sql(sql)

        if rows and len(rows) > 0:
            rate = float(rows[0]['rate'])
            cls._rate_cache[cache_key] = rate
            cls._cache_timestamp = datetime.now()
            return rate

        # Fallback: try inverse rate
        sql_inverse = f"""
        SELECT 1.0 / rate AS rate
        FROM {catalog}.core.latest_exchange_rates
        WHERE from_currency = '{to_currency}'
          AND to_currency = '{from_currency}'
        LIMIT 1
        """

        rows_inverse = await execute_sql(sql_inverse)

        if rows_inverse and len(rows_inverse) > 0:
            rate = float(rows_inverse[0]['rate'])
            cls._rate_cache[cache_key] = rate
            cls._cache_timestamp = datetime.now()
            return rate

        # No rate found - return 1.0 as fallback
        print(f"Warning: No exchange rate found for {from_currency} -> {to_currency}")
        return 1.0

    @classmethod
    def _is_cache_valid(cls) -> bool:
        """Check if exchange rate cache is still valid"""
        if cls._cache_timestamp is None:
            return False

        elapsed_minutes = (datetime.now() - cls._cache_timestamp).total_seconds() / 60
        return elapsed_minutes < cls.CACHE_DURATION_MINUTES

    @classmethod
    async def convert_amount(
        cls,
        amount: float,
        from_currency: str,
        to_currency: str
    ) -> float:
        """
        Convert amount from one currency to another (for display)

        Args:
            amount: Amount in source currency
            from_currency: Source currency
            to_currency: Target currency

        Returns:
            Converted amount
        """
        rate = await cls.get_exchange_rate(from_currency, to_currency)
        return amount * rate

    @classmethod
    async def update_exchange_rate(
        cls,
        from_currency: str,
        to_currency: str,
        rate: float,
        rate_date: date,
        source: str = 'MANUAL'
    ) -> str:
        """
        Update exchange rate in database

        Args:
            from_currency: Source currency
            to_currency: Target currency
            rate: Exchange rate
            rate_date: Date of rate
            source: Rate source ('ECB', 'RBA', 'MANUAL')

        Returns:
            Rate ID
        """
        catalog = get_settings().apex_catalog
        rate_id = str(uuid.uuid4())
        rate_timestamp = datetime.now()

        sql = f"""
        INSERT INTO {catalog}.core.exchange_rates (
            rate_id,
            from_currency,
            to_currency,
            rate,
            rate_date,
            rate_timestamp,
            source,
            is_active,
            created_at
        ) VALUES (
            '{rate_id}',
            '{from_currency}',
            '{to_currency}',
            {rate},
            DATE'{rate_date}',
            TIMESTAMP'{rate_timestamp}',
            '{source}',
            TRUE,
            CURRENT_TIMESTAMP()
        )
        """

        await execute_sql(sql)

        # Invalidate cache
        cls._cache_timestamp = None
        cls._rate_cache.clear()

        return rate_id

    @classmethod
    async def get_market_native_currency(cls, market: str) -> str:
        """
        Get native currency for a market

        Args:
            market: Market code ('NEM', 'EPEX', 'ERCOT')

        Returns:
            Currency code
        """
        market_currencies = {
            'NEM': 'AUD',
            'EPEX': 'EUR',
            'ERCOT': 'USD',
        }

        return market_currencies.get(market.upper(), 'USD')

    @classmethod
    def format_price(
        cls,
        amount: float,
        currency: str,
        include_symbol: bool = True
    ) -> str:
        """
        Format price for display

        Args:
            amount: Price amount
            currency: Currency code
            include_symbol: Include currency symbol

        Returns:
            Formatted string
        """
        # Currency symbols
        symbols = {
            'AUD': '$',
            'EUR': '€',
            'USD': '$',
        }

        symbol = symbols.get(currency, '$')
        formatted = f"{amount:,.2f}"

        if include_symbol:
            return f"{symbol}{formatted}"
        else:
            return f"{formatted} {currency}"


# Singleton instance
currency_service = CurrencyService()


async def initialize_default_rates():
    """
    Initialize default exchange rates (approximate)
    Call this on system startup
    """
    today = date.today()

    # Default rates (should be updated from real sources)
    default_rates = [
        ('AUD', 'EUR', 0.60, 'MANUAL'),  # 1 AUD = 0.60 EUR
        ('AUD', 'USD', 0.65, 'MANUAL'),  # 1 AUD = 0.65 USD
        ('EUR', 'AUD', 1.67, 'MANUAL'),  # 1 EUR = 1.67 AUD
        ('EUR', 'USD', 1.08, 'MANUAL'),  # 1 EUR = 1.08 USD
        ('USD', 'AUD', 1.54, 'MANUAL'),  # 1 USD = 1.54 AUD
        ('USD', 'EUR', 0.93, 'MANUAL'),  # 1 USD = 0.93 EUR
    ]

    for from_curr, to_curr, rate, source in default_rates:
        try:
            await CurrencyService.update_exchange_rate(
                from_curr,
                to_curr,
                rate,
                today,
                source
            )
            print(f"Initialized rate: {from_curr}/{to_curr} = {rate}")
        except Exception as e:
            print(f"Error initializing rate {from_curr}/{to_curr}: {e}")
