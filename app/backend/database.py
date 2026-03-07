from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
import time

import httpx

from app.backend.config import get_settings

_POOL_READY = False


@dataclass
class QueryResult:
    rows: list[dict[str, object]]


async def init_db() -> None:
    global _POOL_READY
    _POOL_READY = True


async def close_db() -> None:
    global _POOL_READY
    _POOL_READY = False


async def lakebase_ping() -> tuple[bool, float]:
    start = time.perf_counter()
    elapsed = (time.perf_counter() - start) * 1000
    return _POOL_READY, elapsed


@asynccontextmanager
async def get_db():
    yield None


async def _execute_statement(statement: str) -> QueryResult:
    settings = get_settings()
    host = settings.databricks_host.rstrip('/')
    token = __import__('os').environ.get('DATABRICKS_TOKEN', '')
    warehouse_id = __import__('os').environ.get('DATABRICKS_SQL_WAREHOUSE_ID', 'a62624c51dced859')
    if not host or not token:
        raise RuntimeError('Live SQL auth not configured')

    headers = {'Authorization': f'Bearer {token}'}
    payload = {
        'statement': statement,
        'warehouse_id': warehouse_id,
        'wait_timeout': '0s',
        'disposition': 'INLINE',
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        create = await client.post(f'{host}/api/2.0/sql/statements', json=payload, headers=headers)
        create.raise_for_status()
        sid = create.json()['statement_id']

        for _ in range(120):
            poll = await client.get(f'{host}/api/2.0/sql/statements/{sid}', headers=headers)
            poll.raise_for_status()
            obj = poll.json()
            state = obj.get('status', {}).get('state')
            if state == 'SUCCEEDED':
                result = obj.get('result', {})
                data = result.get('data_array', [])
                schema = obj.get('manifest', {}).get('schema', {}).get('columns', [])
                names = [c.get('name', f'c{i}') for i, c in enumerate(schema)]
                rows = [dict(zip(names, row)) for row in data]
                return QueryResult(rows=rows)
            if state in {'FAILED', 'CANCELED', 'CLOSED'}:
                message = obj.get('status', {}).get('error', {}).get('message', state)
                raise RuntimeError(f'SQL failed: {message}')
            await __import__('asyncio').sleep(1)

    raise RuntimeError('SQL polling timeout')


async def execute_sql(statement: str) -> list[dict[str, object]]:
    result = await _execute_statement(statement)
    return result.rows
