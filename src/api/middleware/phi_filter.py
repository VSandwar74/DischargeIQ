"""
DischargeIQ PHI Filter Middleware

ASGI middleware that adds Cache-Control: no-store headers to responses
containing PHI (patient and workflow endpoints) and suppresses logging
of request/response bodies for those paths.
"""

import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Paths that return PHI and require protective headers
PHI_PATHS = ("/api/patients", "/api/workflows")


class PHIFilterMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware for PHI-bearing responses.

    - Adds Cache-Control: no-store, Pragma: no-cache to responses on PHI paths.
    - Does NOT log request or response bodies for PHI paths.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        is_phi_path = any(path.startswith(p) for p in PHI_PATHS)

        if is_phi_path:
            # Do NOT log request details for PHI paths
            logger.debug("PHI path accessed: %s (body not logged)", path)

        response = await call_next(request)

        if is_phi_path:
            response.headers["Cache-Control"] = "no-store"
            response.headers["Pragma"] = "no-cache"
            # Do NOT log response body for PHI paths

        return response
