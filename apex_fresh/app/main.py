from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import HTTPException

from apex_fresh.app.backend.routes import router as api_router
from apex_fresh.config import get_config

app = FastAPI(title="APEX Fresh API", version="0.1.0")
app.include_router(api_router)


@app.get("/api/v1/healthz")
def healthz() -> dict[str, str]:
    cfg = get_config()
    return {
        "status": "ok",
        "profile": cfg.profile,
        "catalog": cfg.catalog,
        "app": cfg.app_name,
    }


static_dir = Path(__file__).resolve().parent / "frontend_static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


@app.get("/{full_path:path}")
def spa_fallback(full_path: str) -> FileResponse:
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")
    index_path = static_dir / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="frontend_static/index.html missing")
    return FileResponse(index_path)

