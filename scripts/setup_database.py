#!/usr/bin/env python3
"""
APEX Energy Trading Platform - Database Setup Script

Executes SQL scripts to create the apex_fresh catalog and all schemas/tables.
"""

import os
import sys
from pathlib import Path
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

def split_sql_statements(sql_content: str) -> list[str]:
    """Split SQL content into individual statements, ignoring comments."""
    statements = []
    current_statement = []

    for line in sql_content.split('\n'):
        # Skip comment-only lines
        stripped = line.strip()
        if not stripped or stripped.startswith('--'):
            continue

        current_statement.append(line)

        # Check if line ends with semicolon (statement terminator)
        if stripped.endswith(';'):
            stmt = '\n'.join(current_statement).strip()
            if stmt:
                statements.append(stmt)
            current_statement = []

    # Add any remaining statement
    if current_statement:
        stmt = '\n'.join(current_statement).strip()
        if stmt:
            statements.append(stmt)

    return statements

def execute_sql_file(w: WorkspaceClient, warehouse_id: str, sql_file: Path):
    """Execute a SQL file using Databricks SQL warehouse."""
    print(f"\n{'='*80}")
    print(f"Executing: {sql_file.name}")
    print(f"{'='*80}")

    # Read SQL file
    with open(sql_file, 'r') as f:
        sql_content = f.read()

    # Split into individual statements
    statements = split_sql_statements(sql_content)
    print(f"Found {len(statements)} SQL statements")

    # Execute each statement
    failed = 0
    for idx, statement in enumerate(statements, 1):
        try:
            response = w.statement_execution.execute_statement(
                warehouse_id=warehouse_id,
                statement=statement,
                wait_timeout='30s'
            )

            if response.status.state == StatementState.SUCCEEDED:
                print(f"  ✅ Statement {idx}/{len(statements)}")
            else:
                failed += 1
                print(f"  ❌ Statement {idx}/{len(statements)} FAILED")
                if response.status.error:
                    print(f"     Error: {response.status.error.message}")

        except Exception as e:
            failed += 1
            print(f"  ❌ Statement {idx}/{len(statements)} EXCEPTION")
            print(f"     Error: {str(e)}")

    if failed == 0:
        print(f"✅ SUCCESS: {sql_file.name} (all {len(statements)} statements executed)")
        return True
    else:
        print(f"⚠️  PARTIAL: {sql_file.name} ({failed}/{len(statements)} statements failed)")
        return False

def main():
    """Main execution function."""
    # Initialize Databricks client
    w = WorkspaceClient(profile='DEFAULT')

    # Warehouse ID - use running warehouse from workspace
    warehouse_id = os.environ.get('DATABRICKS_SQL_WAREHOUSE_ID', '01370556fad60fda')

    print("\n" + "="*80)
    print("APEX Energy Trading Platform - Database Setup")
    print("="*80)
    print(f"Workspace: {w.config.host}")
    print(f"Warehouse: {warehouse_id}")
    print("="*80)

    # SQL files to execute in order
    sql_dir = Path(__file__).parent.parent / 'sql' / 'setup'
    sql_files = [
        sql_dir / '00_create_catalog.sql',
        sql_dir / '01_create_schemas.sql',
        sql_dir / '02_create_market_tables.sql',
        sql_dir / '03_create_trading_tables.sql',
        sql_dir / '04_create_risk_tables.sql',
        sql_dir / '05_create_portfolio_tables.sql',
        sql_dir / '06_create_analytics_tables.sql',
    ]

    # Execute each SQL file
    results = []
    for sql_file in sql_files:
        if not sql_file.exists():
            print(f"⚠️  WARNING: File not found: {sql_file}")
            results.append(False)
            continue

        success = execute_sql_file(w, warehouse_id, sql_file)
        results.append(success)

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    total = len(results)
    succeeded = sum(results)
    failed = total - succeeded

    print(f"Total scripts: {total}")
    print(f"✅ Succeeded: {succeeded}")
    print(f"❌ Failed: {failed}")

    if all(results):
        print("\n🎉 Database setup completed successfully!")
        print("\nNext steps:")
        print("  1. Verify catalog: SHOW SCHEMAS IN apex_fresh;")
        print("  2. Load seed data (if needed)")
        print("  3. Restart the apex-etrm app")
        return 0
    else:
        print("\n⚠️  Some scripts failed. Please review the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
