"""
DischargeIQ Workflow API Routes

All endpoints require authentication. Mutations log audit entries
with hashed patient IDs (never raw PHI).
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.data_store import (
    create_workflow,
    get_all_workflows,
    get_workflow,
    update_workflow_status,
)
from src.api.middleware.auth import get_current_user, require_role
from src.security.hashing import hash_identifier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


@router.get("/")
async def list_workflows(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: dict = Depends(get_current_user),
):
    """
    List all discharge workflows, optionally filtered by status.

    Query params:
        status: Filter by workflow status (e.g., AUTH_PENDING, PLACEMENT_SEARCHING)
    """
    workflows = get_all_workflows(status_filter=status_filter)
    return workflows


@router.get("/{workflow_id}")
async def get_workflow_detail(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get a single workflow with nested prior_auth, facility_matches, and audit_trail.
    """
    wf = get_workflow(workflow_id)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    return wf


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_new_workflow(
    body: dict,
    current_user: dict = Depends(
        require_role(["case_manager", "admin", "system_agent"])
    ),
):
    """
    Create a new discharge workflow.

    Body:
        patient_id: str — ID of the patient
        trigger_event: str — What triggered the discharge workflow
    """
    patient_id = body.get("patient_id")
    trigger_event = body.get("trigger_event")

    if not patient_id or not trigger_event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="patient_id and trigger_event are required",
        )

    wf = create_workflow(patient_id, trigger_event)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    # Log with hashed patient ID only
    logger.info(
        "Workflow created: workflow_id=%s patient_hash=%s by user=%s",
        wf["id"],
        hash_identifier(patient_id),
        current_user["user_id"],
    )
    return wf


@router.patch("/{workflow_id}/status")
async def update_status(
    workflow_id: str,
    body: dict,
    current_user: dict = Depends(
        require_role(["case_manager", "admin", "system_agent"])
    ),
):
    """
    Update the status of a workflow.

    Body:
        status: str — New status value
    """
    new_status = body.get("status")
    if not new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="status is required",
        )

    valid_statuses = [
        "INITIATED", "AUTH_PENDING", "AUTH_APPROVED", "AUTH_DENIED",
        "PLACEMENT_SEARCHING", "PLACEMENT_CONFIRMED", "TRANSPORT_SCHEDULED",
        "DISCHARGED", "ESCALATED",
    ]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}",
        )

    wf = update_workflow_status(workflow_id, new_status)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    logger.info(
        "Workflow status updated: workflow_id=%s new_status=%s by user=%s",
        workflow_id,
        new_status,
        current_user["user_id"],
    )
    return wf


@router.post("/{workflow_id}/approve-auth")
async def approve_auth(
    workflow_id: str,
    current_user: dict = Depends(
        require_role(["case_manager", "admin"])
    ),
):
    """
    Case manager approves prior authorization submission for a workflow.
    Transitions workflow from INITIATED/AUTH_PENDING to AUTH_PENDING.
    """
    wf = get_workflow(workflow_id)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    if wf["status"] not in ("INITIATED", "AUTH_PENDING"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve auth for workflow in status {wf['status']}",
        )

    updated = update_workflow_status(workflow_id, "AUTH_PENDING")
    logger.info(
        "Auth approved: workflow_id=%s by user=%s",
        workflow_id,
        current_user["user_id"],
    )
    return updated


@router.post("/{workflow_id}/select-facility")
async def select_facility(
    workflow_id: str,
    body: dict,
    current_user: dict = Depends(
        require_role(["case_manager", "admin"])
    ),
):
    """
    Case manager selects a facility for placement.

    Body:
        facility_id: str — ID of the selected facility match
    """
    facility_id = body.get("facility_id")
    if not facility_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="facility_id is required",
        )

    wf = get_workflow(workflow_id)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    # Update the workflow in-memory
    from src.api.data_store import WORKFLOWS, AUDIT_ENTRIES, _enrich_workflow
    import uuid

    for stored_wf in WORKFLOWS:
        if stored_wf["id"] == workflow_id:
            stored_wf["selected_facility_id"] = facility_id
            stored_wf["status"] = "PLACEMENT_CONFIRMED"
            stored_wf["updated_at"] = datetime.utcnow().isoformat()

            AUDIT_ENTRIES.append({
                "id": str(uuid.uuid4()),
                "workflow_id": workflow_id,
                "patient_id_hash": hash_identifier(stored_wf["patient_id"]),
                "action": "facility_selected",
                "agent": "api",
                "details": {"facility_id": facility_id, "approved_by": current_user["user_id"]},
                "model_version": None,
                "status": "success",
                "user_id": current_user["user_id"],
                "session_id": str(uuid.uuid4()),
                "created_at": datetime.utcnow().isoformat(),
            })

            logger.info(
                "Facility selected: workflow_id=%s facility_id=%s by user=%s",
                workflow_id,
                facility_id,
                current_user["user_id"],
            )
            return _enrich_workflow(stored_wf)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Workflow not found",
    )


@router.post("/{workflow_id}/escalate")
async def escalate_workflow(
    workflow_id: str,
    current_user: dict = Depends(
        require_role(["case_manager", "admin", "system_agent"])
    ),
):
    """
    Escalate a workflow for manual intervention.
    """
    wf = get_workflow(workflow_id)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    if wf["status"] == "DISCHARGED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot escalate a completed workflow",
        )

    updated = update_workflow_status(workflow_id, "ESCALATED")
    logger.info(
        "Workflow escalated: workflow_id=%s by user=%s",
        workflow_id,
        current_user["user_id"],
    )
    return updated
