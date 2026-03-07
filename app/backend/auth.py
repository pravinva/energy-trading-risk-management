from fastapi import Depends, HTTPException, Request
from app.backend.config import get_settings

def get_current_user_email(request: Request) -> str:
    settings = get_settings()
    email = request.headers.get('x-forwarded-email') or settings.nexus_dev_user_email
    if not email:
        raise HTTPException(status_code=401, detail='Missing user identity header')
    return email

def is_databricks_employee(email: str) -> bool:
    return email.lower().endswith('@databricks.com')

def require_databricks_employee(email: str = Depends(get_current_user_email)) -> str:
    if not is_databricks_employee(email):
        raise HTTPException(status_code=403, detail='This feature requires Databricks employee access')
    return email
