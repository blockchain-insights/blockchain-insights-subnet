from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name='x-api-key', auto_error = False)


async def api_key_auth(api_key: str = Security(api_key_header)):
    global api_key_manager
    if api_key_manager is None:
        raise HTTPException(status_code=500, detail="API Key Manager not initialized")
    has_access = await api_key_manager.validate_api_key(api_key)
    if not has_access:
        raise HTTPException(status_code=401, detail="Missing or Invalid API key")