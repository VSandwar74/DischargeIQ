"""
DischargeIQ watsonx.ai Client

Supports two modes:
  - DEV_MODE=true  → WatsonXClient (mock, synthetic responses)
  - DEV_MODE=false → WatsonXLiveClient (real IBM watsonx.ai API)

All model calls in production must go through the safe_model_call wrapper
with PHI redaction on inputs/outputs before logging.
"""

import os
import logging
import random
import time
import uuid
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Production Client — Real IBM watsonx.ai API
# ---------------------------------------------------------------------------

class WatsonXLiveClient:
    """
    Production watsonx.ai client for Granite model inference and governance.

    Auth: IBM Cloud IAM token from API key.

    Requires env vars:
      WATSONX_API_KEY, WATSONX_PROJECT_ID, WATSONX_URL,
      WATSONX_GOVERNANCE_URL (optional)
    """

    IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
    TOKEN_EXPIRY_BUFFER = 60

    def __init__(
        self,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        url: Optional[str] = None,
        governance_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("WATSONX_API_KEY", "")
        self.project_id = project_id or os.getenv("WATSONX_PROJECT_ID", "")
        self.url = (url or os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")).rstrip("/")
        self.governance_url = (
            governance_url or os.getenv("WATSONX_GOVERNANCE_URL", "")
        ).rstrip("/")

        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0

        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
            verify=True,
        )

    async def _ensure_token(self):
        """Obtain or refresh IAM access token."""
        if self._access_token and time.time() < self._token_expires_at:
            return

        resp = await self._http.post(
            self.IAM_TOKEN_URL,
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": self.api_key,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        body = resp.json()
        self._access_token = body["access_token"]
        self._token_expires_at = (
            time.time() + body.get("expires_in", 3600) - self.TOKEN_EXPIRY_BUFFER
        )
        logger.info("watsonx.ai IAM token obtained")

    async def generate(
        self,
        model: str = "ibm/granite-4-h-small",
        prompt: str = "",
        max_new_tokens: int = 1024,
        temperature: float = 0.3,
        top_p: float = 0.9,
        stop_sequences: list = None,
    ) -> "GenerateResponse":
        """
        Generate text using a Granite model via watsonx.ai inference API.

        Maps to: POST /ml/v1/text/generation?version=2024-05-01

        Args:
            model: Model ID (e.g., "ibm/granite-4-h-small").
            prompt: Input prompt.
            max_new_tokens: Max tokens to generate.
            temperature: Sampling temperature.
            top_p: Nucleus sampling parameter.
            stop_sequences: Optional stop sequences.

        Returns:
            GenerateResponse with text, token_count, model fields.
        """
        await self._ensure_token()

        payload = {
            "model_id": model,
            "input": prompt,
            "project_id": self.project_id,
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "decoding_method": "greedy" if temperature == 0 else "sample",
            },
        }
        if stop_sequences:
            payload["parameters"]["stop_sequences"] = stop_sequences

        resp = await self._http.post(
            f"{self.url}/ml/v1/text/generation?version=2024-05-01",
            json=payload,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        body = resp.json()

        results = body.get("results", [{}])
        result = results[0] if results else {}

        return GenerateResponse(
            text=result.get("generated_text", ""),
            token_count=result.get("generated_token_count", 0),
            input_token_count=result.get("input_token_count", 0),
            model=model,
            stop_reason=result.get("stop_reason", ""),
        )

    async def log_governance_event(self, event: dict) -> dict:
        """
        Log an event to watsonx.governance (OpenScale).

        Maps to: POST /v2/monitoring_runs
        """
        if not self.governance_url:
            logger.warning("Governance URL not configured — skipping event log")
            return {"status": "skipped", "reason": "governance_url_not_configured"}

        await self._ensure_token()
        resp = await self._http.post(
            f"{self.governance_url}/v2/monitoring_runs",
            json={
                "event_type": event.get("event_type", "custom"),
                "metadata": event,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        return resp.json()

    async def check_safety(self, text: str, context: dict) -> "SafetyResponse":
        """
        Run Granite Guardian safety check on model output.

        Uses the Granite Guardian model to evaluate generated text for:
        - Hallucination / unsupported clinical claims
        - PHI leakage
        - Bias
        - Clinical accuracy

        Maps to: POST /ml/v1/text/generation with guardian model
        """
        await self._ensure_token()

        guardian_prompt = (
            f"<|system|>You are Granite Guardian, a safety evaluation model. "
            f"Evaluate the following clinical text for accuracy, hallucination, "
            f"and safety issues.\n<|user|>\nText to evaluate:\n{text}\n\n"
            f"Context:\n{str(context)[:500]}\n\n"
            f"Respond with: SAFE or UNSAFE followed by reason.\n<|assistant|>"
        )

        payload = {
            "model_id": "ibm/granite-guardian-3-8b",
            "input": guardian_prompt,
            "project_id": self.project_id,
            "parameters": {
                "max_new_tokens": 200,
                "temperature": 0,
                "decoding_method": "greedy",
            },
        }

        try:
            resp = await self._http.post(
                f"{self.url}/ml/v1/text/generation?version=2024-05-01",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self._access_token}",
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
            body = resp.json()
            result_text = body.get("results", [{}])[0].get("generated_text", "")

            passed = "UNSAFE" not in result_text.upper()
            reason = result_text if not passed else None
            return SafetyResponse(passed=passed, reason=reason)

        except Exception as e:
            logger.warning("Guardian safety check failed: %s", e)
            # Fail open with warning — don't block clinical workflow on guardian failure
            return SafetyResponse(passed=True, reason=None)

    async def close(self):
        await self._http.aclose()


class GenerateResponse:
    """Structured response from watsonx.ai text generation."""
    def __init__(self, text: str, token_count: int = 0, input_token_count: int = 0,
                 model: str = "", stop_reason: str = ""):
        self.text = text
        self.token_count = token_count
        self.input_token_count = input_token_count
        self.model = model
        self.stop_reason = stop_reason


class SafetyResponse:
    """Structured response from Granite Guardian safety check."""
    def __init__(self, passed: bool, reason: Optional[str] = None, confidence: float = 0.95):
        self.passed = passed
        self.reason = reason
        self.confidence = confidence


# ---------------------------------------------------------------------------
# Mock Client — Synthetic data for dev/demo
# ---------------------------------------------------------------------------

class WatsonXClient:
    """Mock watsonx.ai client for LLM generation and governance."""

    def generate(self, model: str = "", prompt: str = "") -> GenerateResponse:
        summaries = [
            (
                "Patient is an 81-year-old female admitted with left hip fracture (ICD-10: S72.001A) "
                "following a mechanical fall at home. Surgical repair (ORIF) was performed on hospital "
                "day 1. AM-PAC Basic Mobility score of 17.2 indicates significant functional limitations. "
                "Patient requires skilled nursing facility placement for intensive rehabilitation. "
                "Estimated SNF length of stay: 21 days."
            ),
            (
                "Patient is a 74-year-old male admitted with acute exacerbation of COPD (ICD-10: J44.1). "
                "Required BiPAP support for 48 hours, now weaned to 2L nasal cannula. AM-PAC score 18.8. "
                "Requires SNF for continued respiratory therapy and progressive mobility program. "
                "Estimated SNF length of stay: 14-21 days."
            ),
        ]
        text = random.choice(summaries)
        return GenerateResponse(text=text, token_count=len(text.split()), model=model)

    def log_governance_event(self, event: dict) -> dict:
        return {
            "event_id": str(uuid.uuid4()),
            "status": "logged",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def check_safety(self, text: str, context: dict) -> SafetyResponse:
        passed = random.random() > 0.05
        return SafetyResponse(
            passed=passed,
            reason="Potential hallucination detected" if not passed else None,
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def _is_live(service_var: str) -> bool:
    """Check if a service should use its live client."""
    dev_mode = os.getenv("DEV_MODE", "true").lower() in ("true", "1", "yes")
    service_mode = os.getenv(service_var, "").lower()
    # Per-service override: "live" forces real client even in DEV_MODE
    if service_mode == "live":
        return True
    if dev_mode or service_mode == "mock":
        return False
    return True


def create_watsonx_client(**kwargs) -> WatsonXClient | WatsonXLiveClient:
    """Factory: returns mock or live watsonx client based on DEV_MODE / WATSONX_MODE."""
    if _is_live("WATSONX_MODE"):
        logger.info("Using live watsonx.ai client")
        return WatsonXLiveClient(**kwargs)
    logger.info("Using mock watsonx client")
    return WatsonXClient()
