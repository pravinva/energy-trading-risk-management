#!/usr/bin/env python3
"""
Generate operational seed data for APEX platform
Creates trades, analytics, and dispatch data
"""
import random
from datetime import datetime, timedelta
from uuid import uuid4
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState


def generate_trades(days=7):
    """Generate sample trades across markets"""
    records = []
    traders = ['alice.wong', 'bob.chen', 'carol.smith', 'david.jones']

    # NEM instruments
    nem_instruments = ['NSW_PEAK_Q2', 'VIC_BASE_Q3', 'QLD_OFFPEAK_Q1', 'SA_CAP_Q4']
    # EPEX instruments
    epex_instruments = ['DE-LU_BASE_Q2', 'FR_PEAK_Q3', 'NL_BASE_Q1']
    # ERCOT instruments
    ercot_instruments = ['ERCOT_NORTH_Q2', 'ERCOT_HOUSTON_Q3', 'ERCOT_WEST_Q1']

    all_instruments = nem_instruments + epex_instruments + ercot_instruments

    start_date = datetime.now() - timedelta(days=days)

    for day in range(days):
        current_date = start_date + timedelta(days=day)

        # 5-15 trades per day
        num_trades = random.randint(5, 15)
        for _ in range(num_trades):
            trade_time = current_date + timedelta(
                hours=random.randint(8, 17),
                minutes=random.randint(0, 59)
            )

            if trade_time > datetime.now():
                continue

            instrument = random.choice(all_instruments)

            # Determine market from instrument
            if instrument.startswith(('NSW_', 'VIC_', 'QLD_', 'SA_')):
                market = 'NEM'
                base_price = random.uniform(70, 120)
            elif instrument.startswith(('DE-LU_', 'FR_', 'NL_')):
                market = 'EPEX'
                base_price = random.uniform(50, 90)
            else:
                market = 'ERCOT'
                base_price = random.uniform(35, 75)

            trade_id = f"TRD-{uuid4().hex[:8].upper()}"
            trader = random.choice(traders)
            side = random.choice(['BUY', 'SELL'])
            volume_mw = round(random.uniform(10, 100), 2)
            price = round(base_price * random.uniform(0.95, 1.05), 2)

            records.append({
                'trade_id': trade_id,
                'market': market,
                'instrument_id': instrument,
                'trader_id': trader,
                'direction': side,
                'volume_mw': volume_mw,
                'price': price,
                'source_system': 'APEX_UI',
                'ingested_at': trade_time.strftime('%Y-%m-%d %H:%M:%S')
            })

    return records


def generate_analytics():
    """Generate sample analytics data"""
    models = []
    backtests = []

    # Model performance
    model_names = ['ARIMA_v2', 'LSTM_v3', 'XGBoost_v1', 'Prophet_v2']
    markets = ['NEM', 'EPEX', 'ERCOT']
    for model in model_names:
        for market in markets:  # One run per market
            run_time = datetime.now() - timedelta(days=random.randint(1, 30))
            models.append({
                'model_name': model,
                'market': market,
                'mape': round(random.uniform(0.05, 0.15), 4),
                'rmse': round(random.uniform(5.0, 15.0), 2),
                'r2': round(random.uniform(0.75, 0.95), 4),
                'run_timestamp': run_time.strftime('%Y-%m-%d %H:%M:%S')
            })

    # Backtest runs
    strategies = ['Mean_Reversion', 'Momentum', 'Arbitrage', 'Statistical_Arb']
    for strategy in strategies:
        for market in markets:  # One run per market
            run_time = datetime.now() - timedelta(days=random.randint(1, 20))
            trades = random.randint(50, 200)
            win_rate = random.uniform(0.52, 0.68)
            total_pnl = round(random.uniform(-5000, 25000), 2)
            sharpe = round(random.uniform(0.8, 2.5), 2)

            backtests.append({
                'strategy': strategy,
                'market': market,
                'trades': trades,
                'win_rate': round(win_rate, 3),
                'total_pnl': total_pnl,
                'sharpe': sharpe,
                'run_timestamp': run_time.strftime('%Y-%m-%d %H:%M:%S')
            })

    return models, backtests


def generate_dispatch_data():
    """Generate dispatch assets and offer bands"""
    assets = []
    offer_bands = []

    # NEM assets
    nem_assets = ['BESS_DALTON', 'BESS_GANNAWARRA', 'BESS_HORNSDALE']
    for asset in nem_assets:
        assets.append({
            'market': 'NEM',
            'asset_id': asset,
            'service_type': 'FCAS_CONTINGENCY'
        })

        # Create offer bands for this asset
        created_at = datetime.now() - timedelta(hours=random.randint(1, 12))
        for band_idx in range(1, 6):  # 5 bands
            offer_bands.append({
                'asset_id': asset,
                'scenario': 'BASE',
                'band_index': band_idx,
                'price': round(random.uniform(50, 150), 2),
                'volume_mw': round(random.uniform(10, 30), 2),
                'created_at': created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

    # ERCOT assets
    ercot_assets = ['BESS_HOUSTON_1', 'BESS_WEST_2']
    for asset in ercot_assets:
        assets.append({
            'market': 'ERCOT',
            'asset_id': asset,
            'service_type': 'ENERGY_ARBITRAGE'
        })

        created_at = datetime.now() - timedelta(hours=random.randint(1, 12))
        for band_idx in range(1, 6):
            offer_bands.append({
                'asset_id': asset,
                'scenario': 'BASE',
                'band_index': band_idx,
                'price': round(random.uniform(30, 100), 2),
                'volume_mw': round(random.uniform(15, 40), 2),
                'created_at': created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

    return assets, offer_bands


def load_trades(w, warehouse_id, catalog, trades):
    """Load trades to Delta table"""
    print(f"\nLoading {len(trades)} trades...")

    values_list = []
    for t in trades:
        values_list.append(
            f"('{t['trade_id']}', '{t['market']}', '{t['instrument_id']}', "
            f"'{t['trader_id']}', '{t['direction']}', {t['volume_mw']}, {t['price']}, "
            f"'{t['source_system']}', TIMESTAMP'{t['ingested_at']}')"
        )

    values_str = ',\n'.join(values_list)
    sql = f"""
    INSERT INTO {catalog}.trading.trades
    (trade_id, market, instrument_id, trader_id, direction, volume_mw, price, source_system, ingested_at)
    VALUES {values_str}
    """

    try:
        response = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=sql,
            wait_timeout='30s'
        )

        if response.status.state == StatementState.SUCCEEDED:
            print(f"  ✅ Loaded {len(trades)} trades")
            return len(trades)
        else:
            print(f"  ❌ Failed to load trades")
            if response.status.error:
                print(f"     Error: {response.status.error.message}")
            return 0
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return 0


def load_analytics(w, warehouse_id, catalog, models, backtests):
    """Load analytics data to Delta tables"""
    print(f"\nLoading {len(models)} model runs...")

    # Create tables first
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {catalog}.analytics.model_performance (
        model_name STRING,
        mape DOUBLE,
        rmse DOUBLE,
        r2 DOUBLE,
        run_timestamp TIMESTAMP
    ) USING DELTA
    """

    try:
        w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=create_sql,
            wait_timeout='30s'
        )
    except Exception as e:
        print(f"  ⚠️  Table creation warning: {str(e)}")

    values_list = []
    for m in models:
        values_list.append(
            f"('{m['model_name']}', '{m['market']}', {m['mape']}, {m['rmse']}, {m['r2']}, "
            f"TIMESTAMP'{m['run_timestamp']}')"
        )

    values_str = ',\n'.join(values_list)
    sql = f"""
    INSERT INTO {catalog}.analytics.model_performance
    (model_name, market, mape, rmse, r2, run_timestamp)
    VALUES {values_str}
    """

    try:
        response = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=sql,
            wait_timeout='30s'
        )

        if response.status.state == StatementState.SUCCEEDED:
            print(f"  ✅ Loaded {len(models)} model runs")
            models_loaded = len(models)
        else:
            print(f"  ❌ Failed to load models")
            models_loaded = 0
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        models_loaded = 0

    # Load backtests
    print(f"\nLoading {len(backtests)} backtest runs...")

    # Create table first
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {catalog}.analytics.backtest_runs (
        strategy STRING,
        trades INT,
        win_rate DOUBLE,
        total_pnl DOUBLE,
        sharpe DOUBLE,
        run_timestamp TIMESTAMP
    ) USING DELTA
    """

    try:
        w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=create_sql,
            wait_timeout='30s'
        )
    except Exception as e:
        print(f"  ⚠️  Table creation warning: {str(e)}")

    values_list = []
    for b in backtests:
        values_list.append(
            f"('{b['strategy']}', '{b['market']}', {b['trades']}, {b['win_rate']}, {b['total_pnl']}, "
            f"{b['sharpe']}, TIMESTAMP'{b['run_timestamp']}')"
        )

    values_str = ',\n'.join(values_list)
    sql = f"""
    INSERT INTO {catalog}.analytics.backtest_runs
    (strategy, market, trades, win_rate, total_pnl, sharpe, run_timestamp)
    VALUES {values_str}
    """

    try:
        response = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=sql,
            wait_timeout='30s'
        )

        if response.status.state == StatementState.SUCCEEDED:
            print(f"  ✅ Loaded {len(backtests)} backtest runs")
            backtests_loaded = len(backtests)
        else:
            print(f"  ❌ Failed to load backtests")
            backtests_loaded = 0
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        backtests_loaded = 0

    return models_loaded + backtests_loaded


def load_dispatch(w, warehouse_id, catalog, assets, offer_bands):
    """Load dispatch data to Delta tables"""
    print(f"\nLoading {len(assets)} dispatch assets...")

    # Create table first
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {catalog}.trading.dispatch_reference (
        market STRING,
        asset_id STRING,
        service_type STRING
    ) USING DELTA
    """

    try:
        w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=create_sql,
            wait_timeout='30s'
        )
    except Exception as e:
        print(f"  ⚠️  Table creation warning: {str(e)}")

    values_list = []
    for a in assets:
        values_list.append(
            f"('{a['market']}', '{a['asset_id']}', '{a['service_type']}')"
        )

    values_str = ',\n'.join(values_list)
    sql = f"""
    INSERT INTO {catalog}.trading.dispatch_reference
    (market, asset_id, service_type)
    VALUES {values_str}
    """

    try:
        response = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=sql,
            wait_timeout='30s'
        )

        if response.status.state == StatementState.SUCCEEDED:
            print(f"  ✅ Loaded {len(assets)} assets")
            assets_loaded = len(assets)
        else:
            print(f"  ❌ Failed to load assets")
            assets_loaded = 0
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        assets_loaded = 0

    # Load offer bands
    print(f"\nLoading {len(offer_bands)} offer bands...")

    # Create table first
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {catalog}.trading.offer_bands (
        asset_id STRING,
        scenario STRING,
        band_index INT,
        price DOUBLE,
        volume_mw DOUBLE,
        created_at TIMESTAMP
    ) USING DELTA
    """

    try:
        w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=create_sql,
            wait_timeout='30s'
        )
    except Exception as e:
        print(f"  ⚠️  Table creation warning: {str(e)}")

    values_list = []
    for o in offer_bands:
        values_list.append(
            f"('{o['asset_id']}', '{o['scenario']}', {o['band_index']}, "
            f"{o['price']}, {o['volume_mw']}, TIMESTAMP'{o['created_at']}')"
        )

    values_str = ',\n'.join(values_list)
    sql = f"""
    INSERT INTO {catalog}.trading.offer_bands
    (asset_id, scenario, band_index, price, volume_mw, created_at)
    VALUES {values_str}
    """

    try:
        response = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=sql,
            wait_timeout='30s'
        )

        if response.status.state == StatementState.SUCCEEDED:
            print(f"  ✅ Loaded {len(offer_bands)} offer bands")
            bands_loaded = len(offer_bands)
        else:
            print(f"  ❌ Failed to load offer bands")
            bands_loaded = 0
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        bands_loaded = 0

    return assets_loaded + bands_loaded


def main():
    """Main operational data seeder"""
    import argparse

    parser = argparse.ArgumentParser(description='Seed APEX operational data')
    parser.add_argument('--days', type=int, default=7, help='Days of trade data to generate')
    parser.add_argument('--catalog', default='apex_fresh', help='Catalog name')
    parser.add_argument('--warehouse-id', default='4b9b953939869799', help='SQL warehouse ID')

    args = parser.parse_args()

    print("=" * 80)
    print("APEX Energy Trading - Operational Data Seeder")
    print("=" * 80)
    print(f"Generating {args.days} days of operational data")
    print(f"Catalog: {args.catalog}")
    print("=" * 80)

    w = WorkspaceClient(profile='DEFAULT')

    # Generate data
    print("\n[1/3] Generating trades...")
    trades = generate_trades(args.days)
    print(f"  Generated {len(trades)} trades")

    print("\n[2/3] Generating analytics data...")
    models, backtests = generate_analytics()
    print(f"  Generated {len(models)} model runs, {len(backtests)} backtest runs")

    print("\n[3/3] Generating dispatch data...")
    assets, offer_bands = generate_dispatch_data()
    print(f"  Generated {len(assets)} assets, {len(offer_bands)} offer bands")

    # Load data
    print("\n" + "=" * 80)
    print("Loading data to Delta tables...")
    print("=" * 80)

    trades_loaded = load_trades(w, args.warehouse_id, args.catalog, trades)
    analytics_loaded = load_analytics(w, args.warehouse_id, args.catalog, models, backtests)
    dispatch_loaded = load_dispatch(w, args.warehouse_id, args.catalog, assets, offer_bands)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Trades loaded:         {trades_loaded:,} / {len(trades):,}")
    print(f"Analytics loaded:      {analytics_loaded:,} / {len(models) + len(backtests):,}")
    print(f"Dispatch data loaded:  {dispatch_loaded:,} / {len(assets) + len(offer_bands):,}")
    print(f"Total records loaded:  {trades_loaded + analytics_loaded + dispatch_loaded:,}")
    print("=" * 80)
    print("\n🎉 Operational data generation complete!")


if __name__ == '__main__':
    main()
