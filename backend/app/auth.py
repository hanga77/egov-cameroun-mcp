from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN

from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(key: str = Security(api_key_header)) -> str:
    if not key or key != settings.api_secret_key:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid or missing API key")
    return key
