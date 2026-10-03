import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app("testing")
    app.config.update(TESTING=True)

    with app.test_client() as client:
        yield client


def test_health_endpoint_returns_200(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200


def test_health_endpoint_returns_json(client):
    response = client.get("/api/v1/health")

    assert response.is_json

    data = response.get_json()

    assert isinstance(data, dict)
    assert data.get("success") is True
