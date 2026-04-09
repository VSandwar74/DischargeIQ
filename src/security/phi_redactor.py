"""
DischargeIQ PHI Redactor

Detects and redacts common PHI patterns from text before logging or external transmission.
Used by audit logging and model I/O safety filters.
"""

import re
from typing import List, Tuple


class PHIRedactor:
    """Redacts common PHI patterns from text strings."""

    PATTERNS: List[Tuple[str, str, re.Pattern]] = [
        (
            "SSN",
            "[REDACTED_SSN]",
            re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        ),
        (
            "PHONE",
            "[REDACTED_PHONE]",
            re.compile(
                r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
            ),
        ),
        (
            "EMAIL",
            "[REDACTED_EMAIL]",
            re.compile(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            ),
        ),
        (
            "DATE",
            "[REDACTED_DATE]",
            re.compile(r"\b\d{2}/\d{2}/\d{4}\b"),
        ),
        (
            "MRN",
            "[REDACTED_ID]",
            re.compile(r"\b\d{7,10}\b"),
        ),
        (
            "MRN",
            "[REDACTED_ID]",
            re.compile(r"\b[A-Z]\d{6,9}\b"),
        ),
    ]

    def redact(self, text: str) -> str:
        """
        Redact all recognized PHI patterns from the given text.

        Args:
            text: Input text that may contain PHI.

        Returns:
            Text with PHI patterns replaced by redaction tokens.
        """
        result = text
        for _name, replacement, pattern in self.PATTERNS:
            result = pattern.sub(replacement, result)
        return result

    def detect(self, text: str) -> List[str]:
        """
        Detect which PHI pattern types are present in the given text.

        Args:
            text: Input text to scan.

        Returns:
            List of pattern names found (e.g., ["SSN", "EMAIL"]).
        """
        found = []
        for name, _replacement, pattern in self.PATTERNS:
            if pattern.search(text):
                found.append(name)
        return found


# Module-level singleton for convenience
phi_redactor = PHIRedactor()
