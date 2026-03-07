from pathlib import Path
from app.backend.config import get_settings
ROOT = Path(__file__).resolve().parents[2]

def load_sql(relative_path: str) -> str:
    sql = (ROOT / relative_path).read_text(encoding='utf-8')
    catalog = get_settings().apex_catalog
    if catalog:
        sql = sql.replace('apex.', f'{catalog}.')
    return sql
