"""
NEMWEB Historical Data Backfill Job
Backfills dispatch prices for a specified date range
"""
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.backend.nemweb.ingestion import NEMWEBIngestionService


async def backfill_date_range(start_date: datetime, end_date: datetime):
    """
    Backfill NEMWEB data for a date range

    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
    """
    service = NEMWEBIngestionService()

    total_days = (end_date - start_date).days + 1
    total_records = 0
    failed_days = []

    print(f"[{datetime.now()}] Starting NEMWEB backfill")
    print(f"  Date range: {start_date.date()} to {end_date.date()}")
    print(f"  Total days: {total_days}")
    print("=" * 80)

    current_date = start_date

    try:
        while current_date <= end_date:
            day_num = (current_date - start_date).days + 1

            print(f"\n[{datetime.now()}] Processing day {day_num}/{total_days}: {current_date.date()}")

            try:
                # Ingest dispatch prices for this date
                result = await service.ingest_dispatch_prices(date=current_date)

                if result['status'] == 'SUCCESS':
                    records_loaded = result.get('records_loaded', 0)
                    total_records += records_loaded
                    print(f"  ✅ SUCCESS - {records_loaded} records loaded")
                else:
                    failed_days.append({
                        'date': current_date.date(),
                        'error': result.get('error_message', 'Unknown error')
                    })
                    print(f"  ❌ FAILED - {result.get('error_message', 'Unknown error')}")

                # Small delay to avoid rate limiting
                await asyncio.sleep(1)

            except Exception as e:
                failed_days.append({
                    'date': current_date.date(),
                    'error': str(e)
                })
                print(f"  ❌ ERROR - {str(e)}")

            current_date += timedelta(days=1)

        # Summary
        print("\n" + "=" * 80)
        print("BACKFILL SUMMARY")
        print("=" * 80)
        print(f"Total days processed: {total_days}")
        print(f"Successful: {total_days - len(failed_days)}")
        print(f"Failed: {len(failed_days)}")
        print(f"Total records loaded: {total_records:,}")

        if failed_days:
            print("\nFailed dates:")
            for failure in failed_days:
                print(f"  - {failure['date']}: {failure['error']}")

        return {
            'total_days': total_days,
            'successful': total_days - len(failed_days),
            'failed': len(failed_days),
            'total_records': total_records,
            'failed_days': failed_days
        }

    finally:
        if service.client:
            await service.client.close()


async def main():
    """Main backfill job"""
    import argparse

    parser = argparse.ArgumentParser(description='Backfill NEMWEB historical data')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--regions', nargs='+', help='Regions to backfill (default: all)')

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
    result = await backfill_date_range(start_date, end_date)

    if result['failed'] > 0:
        print(f"\n⚠️  Backfill completed with {result['failed']} failures")
        sys.exit(1)
    else:
        print(f"\n🎉 Backfill completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
