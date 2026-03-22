#!/usr/bin/env python3
"""
Verify seed data was loaded successfully
"""
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

def verify_data():
    """Query and display data verification"""
    w = WorkspaceClient(profile='DEFAULT')
    warehouse_id = '4b9b953939869799'

    query = """
    SELECT
      'NEM Prices' as market,
      COUNT(*) as total_records,
      COUNT(DISTINCT region_id) as regions,
      MIN(interval_datetime) as earliest_date,
      MAX(interval_datetime) as latest_date
    FROM apex_fresh.market_nem.prices
    UNION ALL
    SELECT
      'EPEX Prices' as market,
      COUNT(*) as total_records,
      COUNT(DISTINCT bidding_zone) as regions,
      MIN(delivery_datetime) as earliest_date,
      MAX(delivery_datetime) as latest_date
    FROM apex_fresh.market_epex.prices
    UNION ALL
    SELECT
      'ERCOT LMP' as market,
      COUNT(*) as total_records,
      COUNT(DISTINCT node_id) as regions,
      MIN(interval_datetime) as earliest_date,
      MAX(interval_datetime) as latest_date
    FROM apex_fresh.market_ercot.lmp
    ORDER BY market
    """

    print("=" * 80)
    print("DATA VERIFICATION REPORT")
    print("=" * 80)

    try:
        response = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=query,
            wait_timeout='30s'
        )

        if response.status.state == StatementState.SUCCEEDED:
            print("\nMarket Data Summary:")
            print("-" * 80)

            if response.result and response.result.data_array:
                # Print header
                print(f"{'Market':<15} {'Records':>12} {'Regions':>8} {'Earliest Date':<20} {'Latest Date':<20}")
                print("-" * 80)

                for row in response.result.data_array:
                    market = row[0]
                    total = int(row[1])
                    regions = int(row[2])
                    earliest = row[3]
                    latest = row[4]
                    print(f"{market:<15} {total:>12,} {regions:>8} {earliest:<20} {latest:<20}")

                # Calculate total
                total_records = sum(int(row[1]) for row in response.result.data_array)
                print("-" * 80)
                print(f"{'TOTAL':<15} {total_records:>12,}")
                print("=" * 80)

                # Validate expected counts
                print("\nValidation:")
                nem_records = int(response.result.data_array[1][1])  # EPEX is first due to ORDER BY
                epex_records = int(response.result.data_array[0][1])
                ercot_records = int(response.result.data_array[2][1])

                expected_nem = 43200  # 5 regions × 288 intervals/day × 30 days
                expected_epex = 3600  # 5 markets × 24 hours/day × 30 days
                expected_ercot = 43200  # 5 hubs × 288 intervals/day × 30 days

                print(f"  NEM:   {nem_records:>6,} / {expected_nem:>6,} expected - {'✅ PASS' if nem_records == expected_nem else '⚠️  DIFF'}")
                print(f"  EPEX:  {epex_records:>6,} / {expected_epex:>6,} expected - {'✅ PASS' if epex_records == expected_epex else '⚠️  DIFF'}")
                print(f"  ERCOT: {ercot_records:>6,} / {expected_ercot:>6,} expected - {'✅ PASS' if ercot_records == expected_ercot else '⚠️  DIFF'}")
                print(f"  TOTAL: {total_records:>6,} / 90,000 expected - {'✅ PASS' if total_records == 90000 else '⚠️  DIFF'}")

                print("\n✅ Data verification complete!")
            else:
                print("⚠️  No data returned from query")
        else:
            print(f"❌ Query failed: {response.status.state}")
            if response.status.error:
                print(f"   Error: {response.status.error.message}")

    except Exception as e:
        print(f"❌ Error verifying data: {str(e)}")

if __name__ == '__main__':
    verify_data()
