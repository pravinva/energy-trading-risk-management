from fastapi import APIRouter, Depends
from app.backend.auth import get_current_user_email, is_databricks_employee
from app.backend.models import APIResponse, UserContextResponse

router = APIRouter(prefix='/api/v1/user', tags=['user'])

@router.get('/me', response_model=APIResponse[UserContextResponse])
async def me(email: str = Depends(get_current_user_email)) -> APIResponse[UserContextResponse]:
    employee = is_databricks_employee(email)
    return APIResponse(data=UserContextResponse(email=email, is_databricks_employee=employee, has_gtm_access=employee))
