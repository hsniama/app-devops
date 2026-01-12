import os
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from app.utils.token_store import get_token_store


def create_jwt(payload: dict, secret_key: str, expires_in: int = 60) -> str:
    if not secret_key:
        raise ValueError("SECRET_KEY no está definido.")

    exp = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    data = dict(payload)
    data.update({"exp": exp, "jti": str(uuid.uuid4())})
    return jwt.encode(data, secret_key, algorithm="HS256")


def verify_jwt(token: str) -> bool:
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise ValueError("SECRET_KEY no está definido.")

    try:
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
        jti = decoded.get("jti")
        exp = decoded.get("exp")
        if not jti or not exp:
            return False

        now = int(datetime.now(timezone.utc).timestamp())
        ttl = int(exp) - now
        if ttl <= 0:
            return False

        store = get_token_store()
        return store.claim_once(f"jwt:{jti}", ttl_seconds=ttl)

    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False
