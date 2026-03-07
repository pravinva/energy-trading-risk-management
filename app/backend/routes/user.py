from fastapi import APIRouter, Depends
from app.backend.auth import get_current_user_email, is_databricks_employee
from app.backend.config import get_settings
from app.backend.database import execute_sql
from app.backend.models import APIResponse, UserContextResponse

router = APIRouter(prefix='/api/v1/user', tags=['user'])

@router.get('/me', response_model=APIResponse[UserContextResponse])
async def me(email: str = Depends(get_current_user_email)) -> APIResponse[UserContextResponse]:
    employee = is_databricks_employee(email)
    return APIResponse(data=UserContextResponse(email=email, is_databricks_employee=employee, has_gtm_access=employee))


@router.get('/traders', response_model=APIResponse[list[str]])
async def traders() -> APIResponse[list[str]]:
    catalog = get_settings().apex_catalog
    rows = await execute_sql(
        f"SELECT DISTINCT trader_id FROM {catalog}.trading.trades "
        f"WHERE trader_id IS NOT NULL AND TRIM(trader_id) <> '' "
        f"ORDER BY trader_id"
    )
    out = [str(r.get("trader_id")) for r in rows if r.get("trader_id")]
    return APIResponse(data=out, region="GLOBAL")
