# app/utils/jwt_handler.py

import os
import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.utils.token_store import get_token_store


def create_jwt(payload: dict, secret_key: str, expires_in: int = 60) -> str:
    """Crea un JWT con expiración (segundos) y jti único."""
    if not secret_key:
        raise ValueError("SECRET_KEY no está definido. Configura variables de entorno.")

    exp_dt = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    payload = dict(payload)
    payload.update(
        {
            "exp": exp_dt,
            "jti": str(uuid.uuid4()),
        }
    )
    return jwt.encode(payload, secret_key, algorithm="HS256")


def verify_jwt(token: str) -> bool:
    """
    Verifica JWT válido y lo hace 'one-time' usando jti.
    - Si ya fue usado: False
    - Si expira o es inválido: False
    """
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise ValueError("SECRET_KEY no está definido. Configura variables de entorno.")

    try:
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
        jti = decoded.get("jti")
        exp = decoded.get("exp")

        if not jti or not exp:
            return False

        now_ts = int(datetime.now(timezone.utc).timestamp())
        ttl = int(exp) - now_ts
        if ttl <= 0:
            return False

        store = get_token_store()
        return store.claim_once(f"jwt:{jti}", ttl_seconds=ttl)

    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False
