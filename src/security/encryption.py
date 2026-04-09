"""
DischargeIQ PHI Encryption

AES-256 encryption via Fernet for PHI at rest.
All patient-identifiable columns are encrypted before database storage.
"""

import os

from cryptography.fernet import Fernet

_key = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
_fernet = Fernet(_key.encode() if isinstance(_key, str) else _key)


def encrypt_phi(plaintext: str) -> str:
    """Encrypt a plaintext string containing PHI. Returns base64-encoded ciphertext."""
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_phi(ciphertext: str) -> str:
    """Decrypt a Fernet-encrypted ciphertext back to plaintext."""
    return _fernet.decrypt(ciphertext.encode()).decode()
