"""
EPEX Historical Data Backfill Job
Backfills day-ahead prices for a specified date range
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.backend.epex.ingestion import EPEXIngestionService


async def backfill_date_range(
    start_date: datetime,
    end_date: datetime,
    market_areas: list[str]
):
    """
    Backfill EPEX data for a date range

    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        market_areas: List of market area codes to backfill
    """
    # Get API key
    api_key = os.environ.get('ENTSOE_API_KEY')
    if not api_key:
        print("ERROR: ENTSOE_API_KEY environment variable not set")
        sys.exit(1)

    service = EPEXIngestionService(api_key)

    total_days = (end_date - start_date).days + 1
    total_records = 0
    failed_items = []

    print(f"[{datetime.now()}] Starting EPEX backfill")
    print(f"  Date range: {start_date.date()} to {end_date.date()}")
    print(f"  Total days: {total_days}")
    print(f"  Market areas: {', '.join(market_areas)}")
    print("=" * 80)

    try:
        for market_area in market_areas:
            print(f"\n{'='*80}")
            print(f"MARKET AREA: {market_area}")
            print('='*80)

            current_date = start_date

            while current_date <= end_date:
                day_num = (current_date - start_date).days + 1

                print(f"\n[{datetime.now()}] Day {day_num}/{total_days}: {current_date.date()}")

                try:
                    result = await service.ingest_day_ahead_prices(
                        market_area=market_area,
                        date=current_date
                    )

                    if result['status'] == 'SUCCESS':
                        records_loaded = result.get('records_loaded', 0)
                        total_records += records_loaded
                        print(f"  ✅ {market_area} - {records_loaded} records loaded")
                    else:
                        failed_items.append({
                            'market_area': market_area,
                            'date': current_date.date(),
                            'error': result.get('error_message', 'Unknown error')
                        })
                        print(f"  ❌ {market_area} - FAILED")

                    # Rate limiting: ENTSOE allows 400 requests per minute
                    # Being conservative with 1 second delay
                    await asyncio.sleep(1)

                except Exception as e:
                    failed_items.append({
                        'market_area': market_area,
                        'date': current_date.date(),
                        'error': str(e)
                    })
                    print(f"  ❌ {market_area} - ERROR: {str(e)}")

                current_date += timedelta(days=1)

            # Longer pause between market areas
            await asyncio.sleep(5)

        # Summary
        print("\n" + "=" * 80)
        print("BACKFILL SUMMARY")
        print("=" * 80)
        print(f"Market areas: {len(market_areas)}")
        print(f"Total days per area: {total_days}")
        print(f"Total operations: {total_days * len(market_areas)}")
        print(f"Successful: {total_days * len(market_areas) - len(failed_items)}")
        print(f"Failed: {len(failed_items)}")
        print(f"Total records loaded: {total_records:,}")

        if failed_items:
            print("\nFailed items:")
            for failure in failed_items:
                print(f"  - {failure['market_area']} {failure['date']}: {failure['error']}")

        return {
            'total_operations': total_days * len(market_areas),
            'successful': total_days * len(market_areas) - len(failed_items),
            'failed': len(failed_items),
            'total_records': total_records,
            'failed_items': failed_items
        }

    finally:
        await service.close()


async def main():
    """Main backfill job"""
    import argparse

    parser = argparse.ArgumentParser(description='Backfill EPEX historical data')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument(
        '--market-areas',
        nargs='+',
        default=['DE', 'FR', 'NL', 'BE', 'AT'],
        help='Market areas to backfill'
    )

    args = parser.parse_args()

    # Parse dates
    start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d')

    if start_date > end_date:
        print("ERROR: start-date must be before end-date")
        sys.exit(1)

    if end_date > datetime.now():
        print("ERROR: end-date cannot be in the future")
        sys.exit(1)

    # Run backfill
    result = await backfill_date_range(start_date, end_date, args.market_areas)

    if result['failed'] > 0:
        print(f"\n⚠️  Backfill completed with {result['failed']} failures")
        sys.exit(1)
    else:
        print(f"\n🎉 Backfill completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
