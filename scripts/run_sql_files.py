import json
import subprocess
import sys
import time
from pathlib import Path

PROFILE = "fe-vm"
WAREHOUSE_ID = "a62624c51dced859"


def sh(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{p.stdout}\n{p.stderr}")
    return p.stdout


def submit(statement: str):
    body = {
        "statement": statement,
        "warehouse_id": WAREHOUSE_ID,
        "wait_timeout": "0s",
        "disposition": "INLINE",
    }
    out = sh(["databricks", "api", "post", "/api/2.0/sql/statements", "--profile", PROFILE, "--json", json.dumps(body), "-o", "json"])
    return json.loads(out)


def poll(statement_id: str):
    for _ in range(180):
        out = sh(["databricks", "api", "get", f"/api/2.0/sql/statements/{statement_id}", "--profile", PROFILE, "-o", "json"])
        obj = json.loads(out)
        state = obj.get("status", {}).get("state")
        if state in {"SUCCEEDED", "FAILED", "CANCELED", "CLOSED"}:
            return obj
        time.sleep(2)
    raise TimeoutError(f"Timed out waiting for {statement_id}")


def split_sql(text: str):
    chunks = []
    cur = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith('--'):
            continue
        cur.append(line)
        if ';' in line:
            q = '\n'.join(cur).strip()
            if q.endswith(';'):
                q = q[:-1]
            if q:
                chunks.append(q)
            cur = []
    tail = '\n'.join(cur).strip()
    if tail:
        chunks.append(tail)
    return chunks


def run_file(path: Path):
    text = path.read_text(encoding='utf-8')
    statements = split_sql(text)
    print(f"Running {path} ({len(statements)} statements)")
    for i, stmt in enumerate(statements, start=1):
        resp = submit(stmt)
        sid = resp["statement_id"]
        res = poll(sid)
        state = res.get("status", {}).get("state")
        if state != "SUCCEEDED":
            raise RuntimeError(f"Statement failed in {path} #{i}: {state}\n{stmt}\n{json.dumps(res)}")


if __name__ == "__main__":
    files = [Path(p) for p in sys.argv[1:]]
    for f in files:
        run_file(f)
    print("DONE")
