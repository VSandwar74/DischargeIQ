"""
DischargeIQ Data Models

SQLAlchemy ORM models for database tables and Pydantic schemas for API responses.
All columns containing PHI are encrypted at rest (AES-256 via Fernet).
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from src.models.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# SQLAlchemy ORM Models
# ---------------------------------------------------------------------------


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True, default=generate_uuid)
    epic_patient_id_encrypted = Column(String, nullable=False)
    name_encrypted = Column(String, nullable=False)
    dob_encrypted = Column(String, nullable=False)
    mrn_encrypted = Column(String, nullable=False)
    coverage_payer_id = Column(String, nullable=True)
    coverage_payer_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    workflows = relationship("DischargeWorkflow", back_populates="patient")


class DischargeWorkflow(Base):
    __tablename__ = "discharge_workflows"

    VALID_STATUSES = [
        "INITIATED",
        "AUTH_PENDING",
        "AUTH_APPROVED",
        "AUTH_DENIED",
        "PLACEMENT_SEARCHING",
        "PLACEMENT_CONFIRMED",
        "TRANSPORT_SCHEDULED",
        "DISCHARGED",
        "ESCALATED",
    ]

    id = Column(String, primary_key=True, default=generate_uuid)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    status = Column(String, nullable=False, default="INITIATED")
    trigger_event = Column(String, nullable=False)
    prior_auth_id = Column(String, nullable=True)
    selected_facility_id = Column(String, nullable=True)
    avoidable_days = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship("Patient", back_populates="workflows")
    prior_auth_records = relationship("PriorAuthRecord", back_populates="workflow")
    facility_matches = relationship("FacilityMatch", back_populates="workflow")
    audit_entries = relationship("AuditEntry", back_populates="workflow")


class PriorAuthRecord(Base):
    __tablename__ = "prior_auth_records"

    id = Column(String, primary_key=True, default=generate_uuid)
    workflow_id = Column(String, ForeignKey("discharge_workflows.id"), nullable=False)
    payer_id = Column(String, nullable=False)
    payer_name = Column(String, nullable=False)
    submission_method = Column(String, nullable=False)  # FHIR_PAS, X12_278, PORTAL_MANUAL
    status = Column(String, nullable=False, default="SUBMITTED")
    tracking_number = Column(String, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    response_at = Column(DateTime, nullable=True)
    denial_reason = Column(String, nullable=True)
    appeal_draft = Column(Text, nullable=True)
    clinical_docs_sent = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    workflow = relationship("DischargeWorkflow", back_populates="prior_auth_records")


class FacilityMatch(Base):
    __tablename__ = "facility_matches"

    id = Column(String, primary_key=True, default=generate_uuid)
    workflow_id = Column(String, ForeignKey("discharge_workflows.id"), nullable=False)
    facility_name = Column(String, nullable=False)
    careport_referral_id = Column(String, nullable=True)
    bed_available = Column(Boolean, default=True)
    accepts_insurance = Column(Boolean, default=True)
    match_score = Column(Integer, default=0)
    distance_miles = Column(Float, default=0.0)
    referral_status = Column(String, default="SENT")  # SENT, ACCEPTED, DECLINED, NO_RESPONSE
    decline_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    workflow = relationship("DischargeWorkflow", back_populates="facility_matches")


class AuditEntry(Base):
    __tablename__ = "audit_entries"

    id = Column(String, primary_key=True, default=generate_uuid)
    workflow_id = Column(String, ForeignKey("discharge_workflows.id"), nullable=True)
    patient_id_hash = Column(String, nullable=False)  # SHA-256 hash, NEVER raw PHI
    action = Column(String, nullable=False)
    agent = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    model_version = Column(String, nullable=True)
    status = Column(String, nullable=False, default="success")
    user_id = Column(String, nullable=False)
    session_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    workflow = relationship("DischargeWorkflow", back_populates="audit_entries")


# ---------------------------------------------------------------------------
# Pydantic Response Schemas
# ---------------------------------------------------------------------------


class PatientResponse(BaseModel):
    id: str
    name: str
    mrn: str
    dob: str
    coverage_payer_id: Optional[str] = None
    coverage_payer_name: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class PriorAuthResponse(BaseModel):
    id: str
    workflow_id: str
    payer_id: str
    payer_name: str
    submission_method: str
    status: str
    tracking_number: Optional[str] = None
    submitted_at: str
    response_at: Optional[str] = None
    denial_reason: Optional[str] = None
    appeal_draft: Optional[str] = None
    clinical_docs_sent: Optional[Any] = None
    created_at: str

    model_config = {"from_attributes": True}


class FacilityMatchResponse(BaseModel):
    id: str
    workflow_id: str
    facility_name: str
    careport_referral_id: Optional[str] = None
    bed_available: bool
    accepts_insurance: bool
    match_score: int
    distance_miles: float
    referral_status: str
    decline_reason: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}


class AuditEntryResponse(BaseModel):
    id: str
    patient_id_hash: str
    action: str
    agent: Optional[str] = None
    details: Optional[Any] = None
    model_version: Optional[str] = None
    status: str
    user_id: str
    session_id: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}


class WorkflowResponse(BaseModel):
    id: str
    patient_id: str
    patient_name: Optional[str] = None
    patient_mrn: Optional[str] = None
    payer_name: Optional[str] = None
    status: str
    trigger_event: str
    prior_auth: Optional[PriorAuthResponse] = None
    facility_matches: list[FacilityMatchResponse] = Field(default_factory=list)
    audit_trail: list[AuditEntryResponse] = Field(default_factory=list)
    avoidable_days: int = 0
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class DashboardSummary(BaseModel):
    auth_pending_count: int
    placed_today_count: int
    avg_delay_days: float
    auth_pending_delta: int
    placed_delta: int
    delay_delta: float


class AlertResponse(BaseModel):
    id: str
    level: str  # URGENT, WARNING, INFO, SUCCESS
    title: str
    message: str
    workflow_id: Optional[str] = None
    created_at: str


class WorkflowCreateRequest(BaseModel):
    patient_id: str
    trigger_event: str


class StatusUpdateRequest(BaseModel):
    status: str
