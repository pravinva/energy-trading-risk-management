import os
import pytest
import requests

@pytest.mark.skipif(not os.getenv('NEXUS_DEPLOYED_URL'), reason='NEXUS_DEPLOYED_URL not provided')
def test_deployed_health() -> None:
    base = os.environ['NEXUS_DEPLOYED_URL'].rstrip('/')
    response = requests.get(f'{base}/api/v1/health/', timeout=15)
    assert response.status_code == 200
