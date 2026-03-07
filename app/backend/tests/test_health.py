from fastapi.testclient import TestClient
from app.backend.app import app

def test_health_endpoint_returns_200() -> None:
    c = TestClient(app)
    assert c.get('/api/v1/health/').status_code == 200

def test_ready_endpoint() -> None:
    c = TestClient(app)
    assert c.get('/api/v1/health/ready').status_code in {200, 503}

def test_user_me_without_auth_header_returns_401() -> None:
    c = TestClient(app)
    assert c.get('/api/v1/user/me').status_code == 401

def test_user_me_returns_employee_true_for_databricks_email() -> None:
    c = TestClient(app)
    assert c.get('/api/v1/user/me', headers={'X-Forwarded-Email': 'test@databricks.com'}).json()['data']['is_databricks_employee'] is True

def test_user_me_returns_employee_false_for_other_email() -> None:
    c = TestClient(app)
    assert c.get('/api/v1/user/me', headers={'X-Forwarded-Email': 'test@customer.com'}).json()['data']['is_databricks_employee'] is False
