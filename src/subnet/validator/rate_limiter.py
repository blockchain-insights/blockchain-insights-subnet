import os
import time
import redis.asyncio
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, redis_url: str, max_requests: int, window_seconds: int):
        super().__init__(app)
        self.redis = redis.asyncio.from_url(redis_url)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        key = f"rate_limiter:{client_ip}"
        current_time = int(time.time())
        pipeline = self.redis.pipeline()

        pipeline.zremrangebyscore(key, 0, current_time - self.window_seconds)
        pipeline.zadd(key, {f"{current_time}:{request.url.path}": current_time})
        pipeline.expire(key, self.window_seconds)
        pipeline.zcard(key)

        _, _, _, count = await pipeline.execute()

        if count > self.max_requests:
            raise HTTPException(status_code=429, detail="Too Many Requests")

        response = await call_next(request)
        return response
