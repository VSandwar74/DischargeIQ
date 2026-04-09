"""
DischargeIQ Authentication & Authorization Middleware

DEV MODE: Accepts "Bearer dev-token-{role}" tokens for easy development.
PROD MODE: Validates JWT tokens using python-jose with HS256.

Roles: case_manager, case_manager_assistant, physician, admin, system_agent
"""

import os
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt

DEV_MODE = os.getenv("DEV_MODE", "true").lower() in ("true", "1", "yes")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-jwt-secret-change-in-production")
JWT_ALGORITHM = "HS256"

VALID_ROLES = {
    "case_manager",
    "case_manager_assistant",
    "physician",
    "admin",
    "system_agent",
}


def _extract_bearer_token(request: Request) -> Optional[str]:
    """Extract Bearer token from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


async def get_current_user(request: Request) -> dict:
    """
    FastAPI dependency that returns the authenticated user dict.

    In dev mode, accepts tokens like "dev-token-case_manager".
    In prod mode, validates JWT and extracts claims.

    Returns:
        User dict with user_id, role, and name.

    Raises:
        HTTPException 401 if authentication fails.
    """
    token = _extract_bearer_token(request)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if DEV_MODE:
        # Dev mode: "dev-token-{role}" format
        if token.startswith("dev-token-"):
            role = token[len("dev-token-"):]
            if role in VALID_ROLES:
                return {
                    "user_id": "dev-user",
                    "role": role,
                    "name": "Demo User",
                }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid dev token. Use format: dev-token-{role}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Production mode: validate JWT
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role")
        name = payload.get("name", "Unknown")

        if not user_id or not role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if role not in VALID_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid role",
            )

        return {
            "user_id": user_id,
            "role": role,
            "name": name,
        }

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(allowed_roles: list):
    """
    FastAPI dependency factory that enforces role-based access control.

    Args:
        allowed_roles: List of roles permitted to access the endpoint.

    Returns:
        Dependency function that validates the user's role.
    """

    async def _check_role(
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user['role']}' not authorized for this action",
            )
        return current_user

    return _check_role
