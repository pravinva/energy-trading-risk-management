#!/usr/bin/env python3
"""
Generate seed data for APEX energy trading platform
Creates realistic synthetic market data for NEM, EPEX, and ERCOT
"""
import random
import uuid
from datetime import datetime, timedelta
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState


def generate_nemweb_prices(days=30):
    """Generate synthetic NEM dispatch prices"""
    records = []
    regions = ['NSW1', 'VIC1', 'QLD1', 'SA1', 'TAS1']

    start_date = datetime.now() - timedelta(days=days)

    # Base prices by region (AUD/MWh)
    base_prices = {
        'NSW1': 80.0,
        'VIC1': 75.0,
        'QLD1': 85.0,
        'SA1': 90.0,
        'TAS1': 70.0
    }

    for day in range(days):
        current_date = start_date + timedelta(days=day)

        # 5-minute intervals (288 per day)
        for interval in range(288):
            interval_datetime = current_date + timedelta(minutes=interval * 5)

            # Skip future dates
            if interval_datetime > datetime.now():
                continue

            for region in regions:
                # Add time-of-day and random variations
                hour = interval_datetime.hour

                # Peak pricing during business hours
                time_factor = 1.0
                if 7 <= hour < 10:  # Morning peak
                    time_factor = 1.4 + random.uniform(-0.1, 0.1)
                elif 17 <= hour < 21:  # Evening peak
                    time_factor = 1.6 + random.uniform(-0.1, 0.1)
                elif 0 <= hour < 6:  # Off-peak
                    time_factor = 0.6 + random.uniform(-0.05, 0.05)

                # Random volatility
                volatility = random.gauss(1.0, 0.15)

                price = base_prices[region] * time_factor * volatility

                # Occasional price spikes
                if random.random() < 0.02:  # 2% chance
                    price *= random.uniform(2.0, 5.0)

                records.append({
                    'interval_datetime': interval_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                    'region_id': region,
                    'rrp': round(price, 2),
                    'data_source': 'SYNTHETIC'
                })

    return records


def generate_epex_prices(days=30):
    """Generate synthetic EPEX day-ahead prices"""
    records = []
    markets = ['DE', 'FR', 'NL', 'BE', 'AT']

    start_date = datetime.now() - timedelta(days=days)

    # Base prices by market (EUR/MWh)
    base_prices = {
        'DE': 65.0,
        'FR': 70.0,
        'NL': 68.0,
        'BE': 67.0,
        'AT': 64.0
    }

    for day in range(days):
        current_date = start_date + timedelta(days=day)

        # Skip future dates
        if current_date.date() > datetime.now().date():
            continue

        for market in markets:
            # Hourly prices (24 per day)
            for hour in range(24):
                delivery_datetime = current_date + timedelta(hours=hour)

                # Time-of-day pricing
                time_factor = 1.0
                if 7 <= hour < 10:
                    time_factor = 1.3
                elif 17 <= hour < 21:
                    time_factor = 1.5
                elif 0 <= hour < 6:
                    time_factor = 0.7

                volatility = random.gauss(1.0, 0.12)
                price = base_prices[market] * time_factor * volatility

                # Negative prices occasionally (renewables)
                if random.random() < 0.01 and 11 <= hour < 16:
                    price = -random.uniform(5, 20)

                records.append({
                    'delivery_datetime': delivery_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                    'bidding_zone': market,
                    'price_eur_mwh': round(price, 2),
                    'mtu_minutes': 60,
                    'data_source': 'SYNTHETIC'
                })

    return records


def generate_ercot_prices(days=30):
    """Generate synthetic ERCOT settlement point prices"""
    records = []
    hubs = ['HB_BUSAVG', 'HB_HOUSTON', 'HB_NORTH', 'HB_SOUTH', 'HB_WEST']

    start_date = datetime.now() - timedelta(days=days)

    # Base prices by hub (USD/MWh)
    base_prices = {
        'HB_BUSAVG': 45.0,
        'HB_HOUSTON': 48.0,
        'HB_NORTH': 44.0,
        'HB_SOUTH': 50.0,
        'HB_WEST': 43.0
    }

    for day in range(days):
        current_date = start_date + timedelta(days=day)

        # 5-minute intervals (288 per day)
        for interval in range(288):
            interval_datetime = current_date + timedelta(minutes=interval * 5)

            if interval_datetime > datetime.now():
                continue

            for hub in hubs:
                hour = interval_datetime.hour

                # ERCOT has extreme volatility
                time_factor = 1.0
                if 14 <= hour < 19:  # Texas afternoon/evening peak
                    time_factor = 1.8 + random.uniform(-0.2, 0.3)
                elif 0 <= hour < 6:
                    time_factor = 0.5 + random.uniform(-0.1, 0.1)

                volatility = random.gauss(1.0, 0.25)  # Higher volatility
                price = base_prices[hub] * time_factor * volatility

                # Extreme price spikes (ERCOT characteristic)
                if random.random() < 0.005:  # 0.5% chance
                    price *= random.uniform(10.0, 50.0)

                records.append({
                    'interval_datetime': interval_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                    'node_id': hub,
                    'lmp': round(price, 2),
                    'rtcb_signal': round(price * random.uniform(0.9, 1.1), 2),
                    'data_source': 'SYNTHETIC'
                })

    return records


def load_data_to_delta(w, warehouse_id, catalog, schema, table, records, batch_size=1000):
    """Load records to Delta table in batches"""
    total_loaded = 0

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]

        # Build VALUES clause
        values_list = []
        for record in batch:
            if table == 'prices' and schema == 'market_nem':
                values_list.append(
                    f"(TIMESTAMP'{record['interval_datetime']}', "
                    f"'{record['region_id']}', {record['rrp']}, '{record['data_source']}')"
                )
            elif table == 'prices' and schema == 'market_epex':
                values_list.append(
                    f"(TIMESTAMP'{record['delivery_datetime']}', "
                    f"'{record['bidding_zone']}', {record['price_eur_mwh']}, "
                    f"{record['mtu_minutes']}, '{record['data_source']}')"
                )
            elif table == 'lmp' and schema == 'market_ercot':
                values_list.append(
                    f"(TIMESTAMP'{record['interval_datetime']}', "
                    f"'{record['node_id']}', {record['lmp']}, "
                    f"{record['rtcb_signal']}, '{record['data_source']}')"
                )

        values_str = ',\n'.join(values_list)

        # INSERT statement
        sql = f"""
        INSERT INTO {catalog}.{schema}.{table}
        VALUES {values_str}
        """

        try:
            response = w.statement_execution.execute_statement(
                warehouse_id=warehouse_id,
                statement=sql,
                wait_timeout='30s'
            )

            if response.status.state == StatementState.SUCCEEDED:
                total_loaded += len(batch)
                print(f"  ✅ Loaded batch {i//batch_size + 1}: {len(batch)} records (total: {total_loaded:,})")
            else:
                print(f"  ❌ Failed batch {i//batch_size + 1}")
                if response.status.error:
                    print(f"     Error: {response.status.error.message}")

        except Exception as e:
            print(f"  ❌ Error loading batch {i//batch_size + 1}: {str(e)}")

    return total_loaded


def main():
    """Main seed data generation"""
    import argparse

    parser = argparse.ArgumentParser(description='Seed APEX market data')
    parser.add_argument('--days', type=int, default=30, help='Days of data to generate')
    parser.add_argument('--catalog', default='apex_fresh', help='Catalog name')
    parser.add_argument('--warehouse-id', default='01370556fad60fda', help='SQL warehouse ID')

    args = parser.parse_args()

    print("=" * 80)
    print("APEX Energy Trading - Market Data Seeder")
    print("=" * 80)
    print(f"Generating {args.days} days of synthetic market data")
    print(f"Catalog: {args.catalog}")
    print("=" * 80)

    w = WorkspaceClient(profile='DEFAULT')

    # Generate data
    print("\n[1/3] Generating NEMWEB data...")
    nemweb_data = generate_nemweb_prices(args.days)
    print(f"  Generated {len(nemweb_data):,} NEM price records")

    print("\n[2/3] Generating EPEX data...")
    epex_data = generate_epex_prices(args.days)
    print(f"  Generated {len(epex_data):,} EPEX price records")

    print("\n[3/3] Generating ERCOT data...")
    ercot_data = generate_ercot_prices(args.days)
    print(f"  Generated {len(ercot_data):,} ERCOT price records")

    # Load data
    print("\n" + "=" * 80)
    print("Loading data to Delta tables...")
    print("=" * 80)

    print("\n[1/3] Loading NEMWEB prices...")
    nem_loaded = load_data_to_delta(
        w, args.warehouse_id, args.catalog, 'market_nem', 'prices',
        nemweb_data, batch_size=500
    )

    print("\n[2/3] Loading EPEX prices...")
    epex_loaded = load_data_to_delta(
        w, args.warehouse_id, args.catalog, 'market_epex', 'prices',
        epex_data, batch_size=500
    )

    print("\n[3/3] Loading ERCOT prices...")
    ercot_loaded = load_data_to_delta(
        w, args.warehouse_id, args.catalog, 'market_ercot', 'lmp',
        ercot_data, batch_size=500
    )

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"NEM prices loaded:    {nem_loaded:,} / {len(nemweb_data):,}")
    print(f"EPEX prices loaded:   {epex_loaded:,} / {len(epex_data):,}")
    print(f"ERCOT prices loaded:  {ercot_loaded:,} / {len(ercot_data):,}")
    print(f"Total records loaded: {nem_loaded + epex_loaded + ercot_loaded:,}")
    print("=" * 80)
    print("\n🎉 Seed data generation complete!")


if __name__ == '__main__':
    main()
