from fastapi import Header, HTTPException, status

from app.config import settings


def require_api_key(x_api_key: str = Header(default="")) -> None:
    """Pass through when APP_API_KEY is unset; enforce match otherwise."""
    if settings.APP_API_KEY and x_api_key != settings.APP_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "https://tools.ietf.org/html/rfc7807",
                "title": "Unauthorized",
                "status": 401,
                "detail": "Invalid or missing X-Api-Key header.",
            },
        )
