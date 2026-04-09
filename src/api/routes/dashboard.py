"""
DischargeIQ Dashboard API Routes

Summary metrics and alerts for the case manager dashboard.
"""

from fastapi import APIRouter, Depends

from src.api.data_store import get_alerts, get_dashboard_summary
from src.api.middleware.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
async def dashboard_summary(
    current_user: dict = Depends(get_current_user),
):
    """
    Return dashboard summary metrics:
    - auth_pending_count
    - placed_today_count
    - avg_delay_days
    - delta values (change from previous period)
    """
    return get_dashboard_summary()


@router.get("/alerts")
async def dashboard_alerts(
    current_user: dict = Depends(get_current_user),
):
    """Return active alerts sorted by most recent first."""
    return get_alerts()
