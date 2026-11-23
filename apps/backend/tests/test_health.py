from http import HTTPStatus


def test_health_returns_ok(client):
    response = client.get("/api/v1/health")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data


def test_readiness_returns_ready_when_db_ok(client_db_ok):
    response = client_db_ok.get("/api/v1/health/ready")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"
    assert "timestamp" in data


def test_readiness_returns_503_when_db_down(client_db_down):
    response = client_db_down.get("/api/v1/health/ready")
    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_health_response_shape(client):
    response = client.get("/api/v1/health")
    data = response.json()
    assert set(data.keys()) == {"status", "version", "timestamp"}


def test_readiness_response_shape_when_db_ok(client_db_ok):
    response = client_db_ok.get("/api/v1/health/ready")
    data = response.json()
    assert set(data.keys()) == {"status", "database", "timestamp"}
