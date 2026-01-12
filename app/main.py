# app/main.py

from typing import Optional
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from app.utils.jwt_handler import create_jwt, verify_jwt

# Local dev only. In Azure/K8s, env vars are injected by Secrets.
load_dotenv()

app = FastAPI()

EXPECTED_API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")


class DevOpsPayload(BaseModel):
    message: str
    to: str
    from_: str = Field(..., alias="from")
    timeToLifeSec: int


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/DevOps")
async def devops_endpoint(
    payload: DevOpsPayload,
    x_parse_rest_api_key: Optional[str] = Header(default=None, alias="X-Parse-REST-API-Key"),
    x_jwt_kwy: Optional[str] = Header(default=None, alias="X-JWT-KWY"),
):
    if not x_parse_rest_api_key or x_parse_rest_api_key != EXPECTED_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")

    if not x_jwt_kwy or not verify_jwt(x_jwt_kwy):
        raise HTTPException(status_code=403, detail="Invalid or missing JWT")

    return {"message": f"Hello {payload.to} your message will be send"}


@app.api_route("/DevOps", methods=["GET", "PUT", "DELETE", "PATCH"])
async def invalid_methods():
    return "ERROR"


@app.get("/generate-jwt")
def generate_jwt_endpoint():
    if not SECRET_KEY:
        raise HTTPException(status_code=500, detail="SECRET_KEY is not set")

    token = create_jwt(
        {"user": "test"},
        secret_key=SECRET_KEY,
        expires_in=604800,  # 7 days
    )
    return {"jwt": token}
