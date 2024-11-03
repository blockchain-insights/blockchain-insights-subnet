import time
import aioredis
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, redis_url: str, max_requests: int, window_seconds: int):
        super().__init__(app)
        self.redis = aioredis.from_url(redis_url)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        key = f"rate_limiter:{client_ip}"
        current_time = int(time.time())

        try:
            pipeline = self.redis.pipeline()
            pipeline.zremrangebyscore(key, 0, current_time - self.window_seconds)
            pipeline.zadd(key, {current_time: current_time})
            pipeline.expire(key, self.window_seconds)
            pipeline.zcard(key)
            results = await pipeline.execute()
            count = results[-1]
            if count > self.max_requests:
                raise HTTPException(status_code=429, detail="Too Many Requests")

        except aioredis.exceptions.ConnectionError:
            raise HTTPException(status_code=500, detail="Redis connection error")

        response = await call_next(request)
        return response