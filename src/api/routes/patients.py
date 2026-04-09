"""
DischargeIQ Patient API Routes

All endpoints require authentication. Responses include
Cache-Control: no-store via PHI filter middleware.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.data_store import get_all_patients, get_patient, get_patient_workflows
from src.api.middleware.auth import get_current_user

router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.get("/")
async def list_patients(
    current_user: dict = Depends(get_current_user),
):
    """List all patients."""
    return get_all_patients()


@router.get("/{patient_id}")
async def get_patient_detail(
    patient_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a single patient by ID."""
    patient = get_patient(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    return patient


@router.get("/{patient_id}/workflows")
async def get_patient_workflow_list(
    patient_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get all workflows for a specific patient."""
    patient = get_patient(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    return get_patient_workflows(patient_id)
