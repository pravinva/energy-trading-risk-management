from fastapi import APIRouter, Depends
from app.backend.auth import require_databricks_employee
from app.backend.gtm import get_plugin
from app.backend.models import APIResponse

router = APIRouter(prefix='/api/v1/gtm', tags=['gtm'])

@router.get('/status', response_model=APIResponse[dict[str, bool]])
async def status() -> APIResponse[dict[str, bool]]:
    plugin = get_plugin()
    available = plugin.is_available()
    return APIResponse(data={'available': available, 'plugin_loaded': available})

@router.get('/signals/{region}', response_model=APIResponse[list[dict]])
async def signals(region: str, _email: str = Depends(require_databricks_employee)) -> APIResponse[list[dict]]:
    plugin = get_plugin()
    if not plugin.is_available():
        return APIResponse(data=[])
    return APIResponse(data=await plugin.get_signals(region))

@router.get('/account/{account_id}', response_model=APIResponse[dict | None])
async def account(account_id: str, _email: str = Depends(require_databricks_employee)) -> APIResponse[dict | None]:
    plugin = get_plugin()
    if not plugin.is_available():
        return APIResponse(data=None)
    return APIResponse(data=await plugin.get_account_detail(account_id))
