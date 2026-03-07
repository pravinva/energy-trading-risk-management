from fastapi.testclient import TestClient
from app.backend.app import app

def test_routes_smoke() -> None:
    c = TestClient(app)
    for ep in ['/api/v1/anz/prices/current','/api/v1/europe/prices/current','/api/v1/americas/prices/current','/api/v1/gtm/status']:
        assert c.get(ep).status_code == 200
