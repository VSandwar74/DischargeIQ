"""
DischargeIQ Workflow Repository

Provides a unified interface for workflow persistence with two backends:
  - InMemoryWorkflowRepo  — for dev/demo (no database needed)
  - PostgresWorkflowRepo  — for production (async SQLAlchemy + PostgreSQL)

Both implement the same async interface so agents don't need to know
which backend is in use.
"""

import os
import logging
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Interface contract (duck typing — both repos implement these methods)
# ---------------------------------------------------------------------------
#
#   async create(workflow: dict) -> dict
#   async get(workflow_id: str) -> Optional[dict]
#   async get_active_by_patient(patient_id: str) -> Optional[dict]
#   async update(workflow_id: str, **fields) -> None
#   async list_all(status: str = None) -> list[dict]
#


# ---------------------------------------------------------------------------
# In-Memory Repository (dev/demo)
# ---------------------------------------------------------------------------

class InMemoryWorkflowRepo:
    """
    In-memory workflow store for development and demo.

    Data lives only for the lifetime of the process. No database required.
    """

    def __init__(self):
        self._workflows: dict[str, dict] = {}

    async def create(self, workflow: dict) -> dict:
        wf_id = workflow.get("id", str(uuid.uuid4()))
        workflow["id"] = wf_id
        workflow.setdefault("status", "INITIATED")
        workflow.setdefault("created_at", datetime.utcnow().isoformat())
        workflow.setdefault("updated_at", datetime.utcnow().isoformat())
        self._workflows[wf_id] = workflow
        return workflow

    async def get(self, workflow_id: str) -> Optional[dict]:
        return self._workflows.get(workflow_id)

    async def get_active_by_patient(self, patient_id: str) -> Optional[dict]:
        terminal = {"DISCHARGED", "CANCELLED"}
        for wf in self._workflows.values():
            if wf.get("patient_id") == patient_id and wf.get("status") not in terminal:
                return wf
        return None

    async def update(self, workflow_id: str, **fields) -> None:
        wf = self._workflows.get(workflow_id)
        if wf:
            wf.update(fields)
            wf["updated_at"] = datetime.utcnow().isoformat()

    async def list_all(self, status: str = None) -> list:
        if status:
            return [wf for wf in self._workflows.values() if wf.get("status") == status]
        return list(self._workflows.values())


# ---------------------------------------------------------------------------
# PostgreSQL Repository (production)
# ---------------------------------------------------------------------------

class PostgresWorkflowRepo:
    """
    Production workflow repository backed by PostgreSQL via async SQLAlchemy.

    Requires an AsyncSession (injected via FastAPI dependency).
    PHI columns are encrypted at the model level (see schemas.py).
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, workflow: dict) -> dict:
        from src.models.schemas import DischargeWorkflow
        from src.security.encryption import encrypt_phi

        wf = DischargeWorkflow(
            id=workflow.get("id", str(uuid.uuid4())),
            patient_id=workflow["patient_id"],
            status=workflow.get("status", "INITIATED"),
            trigger_event=workflow.get("trigger_event", "discharge_order"),
            prior_auth_id=workflow.get("prior_auth_id"),
            selected_facility_id=workflow.get("selected_facility_id"),
            avoidable_days=workflow.get("avoidable_days", 0),
        )
        self._session.add(wf)
        await self._session.flush()

        return self._to_dict(wf)

    async def get(self, workflow_id: str) -> Optional[dict]:
        from src.models.schemas import DischargeWorkflow

        result = await self._session.execute(
            select(DischargeWorkflow).where(DischargeWorkflow.id == workflow_id)
        )
        wf = result.scalar_one_or_none()
        return self._to_dict(wf) if wf else None

    async def get_active_by_patient(self, patient_id: str) -> Optional[dict]:
        from src.models.schemas import DischargeWorkflow

        terminal = ("DISCHARGED", "CANCELLED")
        result = await self._session.execute(
            select(DischargeWorkflow)
            .where(DischargeWorkflow.patient_id == patient_id)
            .where(DischargeWorkflow.status.notin_(terminal))
            .order_by(DischargeWorkflow.created_at.desc())
            .limit(1)
        )
        wf = result.scalar_one_or_none()
        return self._to_dict(wf) if wf else None

    async def update(self, workflow_id: str, **fields) -> None:
        from src.models.schemas import DischargeWorkflow

        fields["updated_at"] = datetime.utcnow()
        await self._session.execute(
            update(DischargeWorkflow)
            .where(DischargeWorkflow.id == workflow_id)
            .values(**fields)
        )
        await self._session.flush()

    async def list_all(self, status: str = None) -> list:
        from src.models.schemas import DischargeWorkflow

        stmt = select(DischargeWorkflow).order_by(DischargeWorkflow.created_at.desc())
        if status:
            stmt = stmt.where(DischargeWorkflow.status == status)

        result = await self._session.execute(stmt)
        return [self._to_dict(wf) for wf in result.scalars().all()]

    @staticmethod
    def _to_dict(wf) -> dict:
        return {
            "id": wf.id,
            "patient_id": wf.patient_id,
            "status": wf.status,
            "trigger_event": wf.trigger_event,
            "prior_auth_id": wf.prior_auth_id,
            "selected_facility_id": wf.selected_facility_id,
            "avoidable_days": wf.avoidable_days,
            "created_at": wf.created_at.isoformat() if wf.created_at else None,
            "updated_at": wf.updated_at.isoformat() if wf.updated_at else None,
        }


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_workflow_repo(session: AsyncSession = None):
    """
    Factory: returns in-memory or Postgres repo based on DEV_MODE.

    Args:
        session: AsyncSession for Postgres (required when DEV_MODE=false).
    """
    if os.getenv("DEV_MODE", "true").lower() in ("true", "1", "yes"):
        return InMemoryWorkflowRepo()
    if session is None:
        raise ValueError("AsyncSession required for production workflow repo")
    return PostgresWorkflowRepo(session)
