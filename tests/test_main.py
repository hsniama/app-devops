# tests/test_main.py

import os

# Set env vars BEFORE importing the app
os.environ.setdefault("API_KEY", "2f5ae96c-b558-4c7b-a590-a501ae1c3f6c")
os.environ.setdefault("SECRET_KEY", "test-secret")

from fastapi.testclient import TestClient 
from app.main import app
from app.utils.jwt_handler import create_jwt  


client = TestClient(app)


def _payload() -> dict:
    return {
        "message": "This is a test",
        "to": "Juan Perez",
        "from": "Rita Asturia",
        "timeToLifeSec": 45,
    }


def test_valid_post_and_token_is_one_time():
    api_key = os.environ["API_KEY"]
    secret_key = os.environ["SECRET_KEY"]

    jwt_token = create_jwt({"user": "test"}, secret_key=secret_key, expires_in=60)

    # First use: OK
    r1 = client.post(
        "/DevOps",
        headers={"X-Parse-REST-API-Key": api_key, "X-JWT-KWY": jwt_token},
        json=_payload(),
    )
    assert r1.status_code == 200
    assert r1.json()["message"] == "Hello Juan Perez your message will be send"

    # Second use (same JWT): must fail (unique per transaction)
    r2 = client.post(
        "/DevOps",
        headers={"X-Parse-REST-API-Key": api_key, "X-JWT-KWY": jwt_token},
        json=_payload(),
    )
    assert r2.status_code == 403
    assert r2.json()["detail"] == "Invalid or missing JWT"


def test_missing_api_key():
    secret_key = os.environ["SECRET_KEY"]
    jwt_token = create_jwt({"user": "test"}, secret_key=secret_key, expires_in=60)

    response = client.post(
        "/DevOps",
        headers={"X-JWT-KWY": jwt_token},
        json=_payload(),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API Key"


def test_invalid_jwt():
    api_key = os.environ["API_KEY"]

    response = client.post(
        "/DevOps",
        headers={"X-Parse-REST-API-Key": api_key, "X-JWT-KWY": "invalid.token.value"},
        json=_payload(),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid or missing JWT"


def test_invalid_method_get():
    response = client.get("/DevOps")
    assert response.status_code == 200
    assert response.text == '"ERROR"'


def test_generate_jwt():
    response = client.get("/generate-jwt")
    assert response.status_code == 200
    assert "jwt" in response.json()


def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
