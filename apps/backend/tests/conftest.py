from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def client_db_ok(client):
    with patch("app.api.v1.routes.health.check_db_connection", return_value=True):
        yield client


@pytest.fixture
def client_db_down(client):
    with patch("app.api.v1.routes.health.check_db_connection", return_value=False):
        yield client
