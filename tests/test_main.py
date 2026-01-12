# app/utils/token_store.py

import os
import time
from functools import lru_cache
from typing import Optional

try:
    import redis  # type: ignore
except Exception:
    redis = None


class TokenStore:
    """Abstracción: permite marcar un token como usado 1 sola vez con TTL."""
    def claim_once(self, key: str, ttl_seconds: int) -> bool:
        raise NotImplementedError


class InMemoryTokenStore(TokenStore):
    """
    Fallback para local/tests si no hay Redis.
    NO sirve para multi-pod (en k8s debes usar Redis).
    """
    def __init__(self) -> None:
        self._used: dict[str, float] = {}

    def claim_once(self, key: str, ttl_seconds: int) -> bool:
        now = time.time()

        # Purga expirados
        expired_keys = [k for k, exp in self._used.items() if exp <= now]
        for k in expired_keys:
            self._used.pop(k, None)

        if key in self._used:
            return False

        self._used[key] = now + ttl_seconds
        return True


class RedisTokenStore(TokenStore):
    def __init__(self, url: str) -> None:
        if redis is None:
            raise RuntimeError("redis package not installed. Add redis to requirements.txt")
        self._r = redis.Redis.from_url(url, decode_responses=True)

    def claim_once(self, key: str, ttl_seconds: int) -> bool:
        # SET key "1" NX EX <ttl>
        ok = self._r.set(name=key, value="1", nx=True, ex=ttl_seconds)
        return bool(ok)


@lru_cache(maxsize=1)
def get_token_store() -> TokenStore:
    """
    Devuelve SIEMPRE la misma instancia (singleton) por proceso.
    - En k8s: usa Redis si REDIS_URL está set.
    - En tests/local: usa memoria si no hay REDIS_URL.
    """
    url: Optional[str] = os.getenv("REDIS_URL")
    if url:
        return RedisTokenStore(url)
    return InMemoryTokenStore()
