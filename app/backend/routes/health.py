from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.backend.config import get_settings
from app.backend.database import lakebase_ping
from app.backend.models import APIResponse, HealthResponse

router = APIRouter(prefix='/api/v1/health', tags=['health'])

@router.get('/', response_model=APIResponse[HealthResponse])
async def health() -> APIResponse[HealthResponse]:
    settings = get_settings()
    connected, _ = await lakebase_ping()
    return APIResponse(data=HealthResponse(status='ok' if connected else 'degraded', version=settings.app_version, environment=settings.nexus_environment, lakebase_connected=connected))

@router.get('/lakebase', response_model=APIResponse[dict[str, object]])
async def lakebase() -> APIResponse[dict[str, object]]:
    connected, elapsed = await lakebase_ping()
    return APIResponse(data={'lakebase_connected': connected, 'query_time_ms': round(elapsed, 3), 'regions_count': 3})

@router.get('/ready')
async def ready() -> JSONResponse:
    connected, _ = await lakebase_ping()
    return JSONResponse({'ready': connected}, status_code=status.HTTP_200_OK if connected else status.HTTP_503_SERVICE_UNAVAILABLE)
