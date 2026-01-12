import os
import time
from typing import Optional

try:
    import redis  # type: ignore
except Exception:
    redis = None


class TokenStore:
    def claim_once(self, key: str, ttl_seconds: int) -> bool:
        raise NotImplementedError


class InMemoryTokenStore(TokenStore):
    """
    Store de fallback para local/tests.
    IMPORTANTE: debe vivir como singleton para que recuerde tokens usados.
    """
    def __init__(self) -> None:
        self._used: dict[str, float] = {}

    def claim_once(self, key: str, ttl_seconds: int) -> bool:
        now = time.time()

        # Purga expirados
        expired = [k for k, exp in self._used.items() if exp <= now]
        for k in expired:
            self._used.pop(k, None)

        if key in self._used:
            return False

        self._used[key] = now + ttl_seconds
        return True


class RedisTokenStore(TokenStore):
    def __init__(self, url: str) -> None:
        if redis is None:
            raise RuntimeError("redis package not installed")
        self._r = redis.Redis.from_url(url, decode_responses=True)

    def claim_once(self, key: str, ttl_seconds: int) -> bool:
        # SET key 1 NX EX <ttl>
        ok = self._r.set(name=key, value="1", nx=True, ex=ttl_seconds)
        return bool(ok)


# ✅ Singleton cache
_STORE: Optional[TokenStore] = None
_STORE_URL: Optional[str] = None


def get_token_store() -> TokenStore:
    """
    Devuelve SIEMPRE el mismo store mientras el proceso viva.
    Si cambia REDIS_URL entre llamadas, recrea el store (útil en tests).
    """
    global _STORE, _STORE_URL

    url = os.getenv("REDIS_URL")

    if _STORE is not None and url == _STORE_URL:
        return _STORE

    _STORE_URL = url

    if url:
        _STORE = RedisTokenStore(url)
    else:
        _STORE = InMemoryTokenStore()

    return _STORE


def reset_token_store_for_tests() -> None:
    """Útil si quieres limpiar estado entre tests."""
    global _STORE, _STORE_URL
    _STORE = None
    _STORE_URL = None
