"""Tests for DischargeIQ security module. All data is synthetic."""
import os
import sys
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set required env vars before importing
os.environ.setdefault("ENCRYPTION_KEY", "H1AUtHiZBOdOQyxunrAEKJGZaaNzVZtW1S4LR6tEIzM=")  # test key
os.environ.setdefault("AUDIT_SALT", "test-salt-for-unit-tests")

from src.security.encryption import encrypt_phi, decrypt_phi
from src.security.hashing import hash_identifier
from src.security.phi_redactor import PHIRedactor


class TestEncryption:
    def test_encrypt_decrypt_roundtrip(self):
        original = "Jane Smith"
        encrypted = encrypt_phi(original)
        assert encrypted != original
        decrypted = decrypt_phi(encrypted)
        assert decrypted == original

    def test_encrypt_produces_different_ciphertext(self):
        """Fernet uses a timestamp + IV so same plaintext gives different ciphertext."""
        a = encrypt_phi("test")
        b = encrypt_phi("test")
        assert a != b  # different due to IV/timestamp


class TestHashing:
    def test_hash_deterministic(self):
        h1 = hash_identifier("patient-123")
        h2 = hash_identifier("patient-123")
        assert h1 == h2

    def test_hash_salted_differs_from_plain(self):
        import hashlib
        plain_hash = hashlib.sha256("patient-123".encode()).hexdigest()
        salted_hash = hash_identifier("patient-123")
        assert plain_hash != salted_hash

    def test_hash_different_inputs(self):
        h1 = hash_identifier("patient-123")
        h2 = hash_identifier("patient-456")
        assert h1 != h2


class TestPHIRedactor:
    def setup_method(self):
        self.redactor = PHIRedactor()

    def test_redact_ssn(self):
        text = "Patient SSN is 123-45-6789"
        result = self.redactor.redact(text)
        assert "123-45-6789" not in result
        assert "[REDACTED_SSN]" in result

    def test_redact_phone(self):
        text = "Call patient at (555) 123-4567"
        result = self.redactor.redact(text)
        assert "555" not in result or "123-4567" not in result
        assert "[REDACTED_PHONE]" in result

    def test_redact_email(self):
        text = "Contact at jane.smith@hospital.org"
        result = self.redactor.redact(text)
        assert "jane.smith@hospital.org" not in result
        assert "[REDACTED_EMAIL]" in result

    def test_preserves_non_phi(self):
        text = "Patient requires SNF placement for rehabilitation"
        result = self.redactor.redact(text)
        assert result == text
