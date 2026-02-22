"""API key validation middleware for WordPress integration."""

from fastapi import HTTPException, Request

from ..config import WP_API_KEY


async def validate_api_key(request: Request) -> None:
    """Validate the X-API-Key header against the configured WP_API_KEY.

    Raises:
        HTTPException: 401 if the key is missing or invalid.
    """
    if not WP_API_KEY:
        # No API key configured — skip validation (development mode)
        return

    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key != WP_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
        )
