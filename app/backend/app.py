from contextlib import asynccontextmanager
from pathlib import Path
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.backend.config import get_settings
from app.backend.database import close_db, init_db
from app.backend.gtm import load_plugin_if_available
from app.backend.routes import router

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    load_plugin_if_available()
    await init_db()
    logger.info('Starting APEX API workspace=%s env=%s lakebase_host=%s', settings.databricks_host, settings.apex_environment, settings.lakebase_host)
    yield
    await close_db()

app = FastAPI(title='APEX API', version='1.0.0', lifespan=lifespan)
settings = get_settings()
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
app.include_router(router)

static_dir = Path(__file__).resolve().parent / 'static'
if static_dir.exists():
    app.mount('/', StaticFiles(directory=static_dir, html=True), name='static')

@app.get('/{full_path:path}')
def spa_fallback(full_path: str) -> FileResponse:
    if full_path.startswith('api/'):
        raise HTTPException(status_code=404, detail='API route not found')
    index_file = static_dir / 'index.html'
    if not index_file.exists():
        raise HTTPException(status_code=404, detail='Frontend build output not found')
    return FileResponse(index_file)
