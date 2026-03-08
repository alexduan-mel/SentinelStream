from __future__ import annotations

import os
from dataclasses import dataclass

import redis


@dataclass(frozen=True)
class RedisTokenBucket:
    client: redis.Redis
    key: str

    _LUA_CONSUME = (
        "local key = KEYS[1]\n"
        "local count = tonumber(ARGV[1]) or 1\n"
        "local tokens = tonumber(redis.call('GET', key) or '0')\n"
        "if tokens < count then return -1 end\n"
        "tokens = tokens - count\n"
        "redis.call('SET', key, tokens)\n"
        "return tokens"
    )

    @classmethod
    def create(cls, key: str) -> "RedisTokenBucket":
        host = os.getenv("REDIS_HOST", "redis")
        port = int(os.getenv("REDIS_PORT", "6379"))
        db = int(os.getenv("REDIS_DB", "0"))
        password = os.getenv("REDIS_PASSWORD")
        client = redis.Redis(host=host, port=port, db=db, password=password, decode_responses=True)
        # Verify connectivity early
        client.ping()
        return cls(client=client, key=key)

    def reset(self, tokens: int) -> None:
        self.client.set(self.key, int(tokens))

    def remaining(self) -> int:
        value = self.client.get(self.key)
        try:
            return int(value) if value is not None else 0
        except (TypeError, ValueError):
            return 0

    def consume(self, count: int = 1) -> int:
        if count <= 0:
            return self.remaining()
        result = self.client.eval(self._LUA_CONSUME, 1, self.key, int(count))
        try:
            return int(result)
        except (TypeError, ValueError):
            return -1
