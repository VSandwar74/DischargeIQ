"""Initial DischargeIQ schema

Revision ID: 001
Revises:
Create Date: 2026-04-09

All PHI columns (name, DOB, MRN, Epic ID) are stored encrypted.
Encryption/decryption happens at the application layer via Fernet (AES-256).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Patients (PHI columns are encrypted at application layer) --
    op.create_table(
        "patients",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("epic_patient_id_encrypted", sa.String(), nullable=False),
        sa.Column("name_encrypted", sa.String(), nullable=False),
        sa.Column("dob_encrypted", sa.String(), nullable=False),
        sa.Column("mrn_encrypted", sa.String(), nullable=False),
        sa.Column("coverage_payer_id", sa.String(), nullable=True),
        sa.Column("coverage_payer_name", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # -- Discharge Workflows --
    op.create_table(
        "discharge_workflows",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="INITIATED"),
        sa.Column("trigger_event", sa.String(), nullable=False),
        sa.Column("prior_auth_id", sa.String(), nullable=True),
        sa.Column("selected_facility_id", sa.String(), nullable=True),
        sa.Column("avoidable_days", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_workflows_patient_id", "discharge_workflows", ["patient_id"])
    op.create_index("ix_workflows_status", "discharge_workflows", ["status"])

    # -- Prior Auth Records --
    op.create_table(
        "prior_auth_records",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("workflow_id", sa.String(), sa.ForeignKey("discharge_workflows.id"), nullable=False),
        sa.Column("payer_id", sa.String(), nullable=False),
        sa.Column("payer_name", sa.String(), nullable=False),
        sa.Column("submission_method", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="SUBMITTED"),
        sa.Column("tracking_number", sa.String(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("response_at", sa.DateTime(), nullable=True),
        sa.Column("denial_reason", sa.String(), nullable=True),
        sa.Column("appeal_draft", sa.Text(), nullable=True),
        sa.Column("clinical_docs_sent", JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_pa_workflow_id", "prior_auth_records", ["workflow_id"])
    op.create_index("ix_pa_tracking", "prior_auth_records", ["tracking_number"])

    # -- Facility Matches --
    op.create_table(
        "facility_matches",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("workflow_id", sa.String(), sa.ForeignKey("discharge_workflows.id"), nullable=False),
        sa.Column("facility_name", sa.String(), nullable=False),
        sa.Column("careport_referral_id", sa.String(), nullable=True),
        sa.Column("bed_available", sa.Boolean(), server_default="true"),
        sa.Column("accepts_insurance", sa.Boolean(), server_default="true"),
        sa.Column("match_score", sa.Integer(), server_default="0"),
        sa.Column("distance_miles", sa.Float(), server_default="0.0"),
        sa.Column("referral_status", sa.String(), server_default="SENT"),
        sa.Column("decline_reason", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_fm_workflow_id", "facility_matches", ["workflow_id"])

    # -- Audit Entries (HIPAA: 6-year retention, immutable) --
    op.create_table(
        "audit_entries",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("workflow_id", sa.String(), sa.ForeignKey("discharge_workflows.id"), nullable=True),
        sa.Column("patient_id_hash", sa.String(64), nullable=False),  # SHA-256, never raw PHI
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("agent", sa.String(), nullable=True),
        sa.Column("details", JSON(), nullable=True),
        sa.Column("model_version", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="success"),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_patient_hash", "audit_entries", ["patient_id_hash"])
    op.create_index("ix_audit_created_at", "audit_entries", ["created_at"])
    op.create_index("ix_audit_agent", "audit_entries", ["agent"])


def downgrade() -> None:
    op.drop_table("audit_entries")
    op.drop_table("facility_matches")
    op.drop_table("prior_auth_records")
    op.drop_table("discharge_workflows")
    op.drop_table("patients")
