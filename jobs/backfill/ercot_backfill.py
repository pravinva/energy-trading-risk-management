"""
ERCOT Historical Data Backfill Job
Backfills real-time Settlement Point Prices for a specified date range
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.backend.ercot.ingestion import ERCOTIngestionService


async def backfill_date_range(
    start_date: datetime,
    end_date: datetime,
    settlement_points: list[str]
):
    """
    Backfill ERCOT data for a date range

    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        settlement_points: List of settlement point codes to backfill
    """
    api_key = os.environ.get('ERCOT_API_KEY')
    service = ERCOTIngestionService(api_key)

    total_days = (end_date - start_date).days + 1
    total_records = 0
    failed_items = []

    print(f"[{datetime.now()}] Starting ERCOT backfill")
    print(f"  Date range: {start_date.date()} to {end_date.date()}")
    print(f"  Total days: {total_days}")
    print(f"  Settlement points: {', '.join(settlement_points)}")
    print("=" * 80)

    try:
        for settlement_point in settlement_points:
            print(f"\n{'='*80}")
            print(f"SETTLEMENT POINT: {settlement_point}")
            print('='*80)

            current_date = start_date

            while current_date <= end_date:
                day_num = (current_date - start_date).days + 1

                print(f"\n[{datetime.now()}] Day {day_num}/{total_days}: {current_date.date()}")

                try:
                    # Backfill in 6-hour chunks to avoid overwhelming the API
                    for hour_offset in [0, 6, 12, 18]:
                        chunk_start = current_date.replace(
                            hour=hour_offset, minute=0, second=0
                        )

                        result = await service.ingest_real_time_prices(
                            settlement_point=settlement_point,
                            lookback_hours=6
                        )

                        if result['status'] == 'SUCCESS':
                            records_loaded = result.get('records_loaded', 0)
                            total_records += records_loaded
                            print(f"  ✅ {settlement_point} {chunk_start.hour:02d}:00 - {records_loaded} records")
                        else:
                            failed_items.append({
                                'settlement_point': settlement_point,
                                'date': current_date.date(),
                                'hour': hour_offset,
                                'error': result.get('error_message', 'Unknown error')
                            })
                            print(f"  ❌ {settlement_point} {chunk_start.hour:02d}:00 - FAILED")

                        # Rate limiting
                        await asyncio.sleep(2)

                except Exception as e:
                    failed_items.append({
                        'settlement_point': settlement_point,
                        'date': current_date.date(),
                        'error': str(e)
                    })
                    print(f"  ❌ {settlement_point} - ERROR: {str(e)}")

                current_date += timedelta(days=1)

            # Longer pause between settlement points
            await asyncio.sleep(5)

        # Summary
        print("\n" + "=" * 80)
        print("BACKFILL SUMMARY")
        print("=" * 80)
        print(f"Settlement points: {len(settlement_points)}")
        print(f"Total days per point: {total_days}")
        print(f"Total operations: {total_days * len(settlement_points) * 4}")  # 4 chunks per day
        print(f"Successful: {total_days * len(settlement_points) * 4 - len(failed_items)}")
        print(f"Failed: {len(failed_items)}")
        print(f"Total records loaded: {total_records:,}")

        if failed_items:
            print("\nFailed items:")
            for failure in failed_items[:20]:  # Show first 20
                print(f"  - {failure['settlement_point']} {failure['date']}: {failure['error']}")
            if len(failed_items) > 20:
                print(f"  ... and {len(failed_items) - 20} more failures")

        return {
            'total_operations': total_days * len(settlement_points) * 4,
            'successful': total_days * len(settlement_points) * 4 - len(failed_items),
            'failed': len(failed_items),
            'total_records': total_records,
            'failed_items': failed_items
        }

    finally:
        await service.close()


async def main():
    """Main backfill job"""
    import argparse

    parser = argparse.ArgumentParser(description='Backfill ERCOT historical data')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument(
        '--settlement-points',
        nargs='+',
        default=['HB_BUSAVG', 'HB_HOUSTON', 'HB_NORTH', 'HB_SOUTH', 'HB_WEST'],
        help='Settlement points to backfill'
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
    result = await backfill_date_range(start_date, end_date, args.settlement_points)

    if result['failed'] > 0:
        print(f"\n⚠️  Backfill completed with {result['failed']} failures")
        sys.exit(1)
    else:
        print(f"\n🎉 Backfill completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
