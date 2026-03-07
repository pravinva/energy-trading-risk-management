from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]

def load_sql(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding='utf-8')
