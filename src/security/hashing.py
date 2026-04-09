"""
DischargeIQ Identifier Hashing

SHA-256 with salt for audit log entries.
Patient identifiers are hashed before writing to audit logs per HIPAA requirements.
Raw PHI is NEVER stored in audit records.
"""

import hashlib
import os

AUDIT_SALT = os.getenv("AUDIT_SALT", "dischargeiq-dev-salt-change-in-production")


def hash_identifier(value: str) -> str:
    """
    Hash a patient identifier using SHA-256 with salt.

    Args:
        value: The raw identifier (e.g., patient ID, MRN).

    Returns:
        Hex digest of the salted SHA-256 hash.
    """
    salted = f"{AUDIT_SALT}{value}".encode("utf-8")
    return hashlib.sha256(salted).hexdigest()
