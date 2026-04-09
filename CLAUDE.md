# CLAUDE.md — DischargeIQ

## Project Overview

DischargeIQ is an agentic AI system that automates hospital discharge coordination for Medicare Advantage skilled nursing facility (SNF) placements. It runs on IBM watsonx (Orchestrate, Granite 4.0, watsonx.governance) with Epic FHIR and Availity integrations.

**Read these docs before starting any work:**
- `docs/DischargeIQ_Product_Design_Doc.md` — full architecture, agent specs, data models, integration details
- `docs/DischargeIQ_Frontend_Design_Principles.md` — IBM Carbon design system, color tokens, component patterns

---

## HIPAA Compliance Rules — MANDATORY

These rules apply to ALL code in this project. Every function, endpoint, log statement, database query, and API call must comply. Violations are not acceptable even in development, testing, or demo environments.

### 1. Protected Health Information (PHI) — Definition

PHI includes any individually identifiable health information. In this codebase, PHI includes but is not limited to:
- Patient names, MRNs, dates of birth, SSNs, addresses, phone numbers, email addresses
- Medical record numbers, encounter IDs, account numbers
- Diagnosis codes (ICD-10) when linked to a patient identifier
- Therapy scores (AMPAC), functional assessments
- Insurance member IDs, policy numbers, authorization tracking numbers
- Facility placement details linked to a patient
- Any FHIR resource fetched from Epic that contains patient data

### 2. PHI Handling Rules

```
NEVER:
- Log raw PHI to console, files, or any logging service
- Store PHI in plaintext in any database column
- Include PHI in error messages, stack traces, or exception handlers
- Commit PHI (real or realistic fake) to version control
- Pass PHI in URL query parameters
- Store PHI in browser localStorage, sessionStorage, or cookies
- Include PHI in analytics, telemetry, or crash reports
- Use real patient data in tests — always use synthetic/de-identified data
- Return PHI in API error responses

ALWAYS:
- Hash patient identifiers (SHA-256 + salt) before writing to audit logs
- Encrypt PHI at rest using AES-256
- Encrypt PHI in transit using TLS 1.3
- Use parameterized queries — never interpolate PHI into SQL strings
- Sanitize all model inputs and outputs through PII/PHI filters before logging
- Apply minimum necessary principle — only fetch the FHIR resources needed for the task
- Set appropriate Cache-Control headers (no-store) on responses containing PHI
```

### 3. Audit Logging

Every agent action that touches PHI must produce an audit record. This is a HIPAA requirement with 6-year retention.

```python
# CORRECT audit log entry
audit_entry = {
    "timestamp": datetime.utcnow().isoformat(),
    "patient_id_hash": sha256_hash(patient_id, salt=AUDIT_SALT),
    "action": "prior_auth_submitted",
    "agent": "prior_auth_agent",
    "payer": "aetna_medicare",  # payer name is not PHI
    "model_version": "granite-4-h-small-v1.2",
    "input_token_count": 1842,
    "output_token_count": 456,
    "status": "success",
    "user_id": case_manager_id,  # who triggered/approved the action
    "session_id": session_id
}

# WRONG — contains raw PHI
audit_entry = {
    "patient_name": "Jane Smith",        # VIOLATION
    "mrn": "12345678",                   # VIOLATION
    "diagnosis": "hip fracture S72.001A" # VIOLATION when linked to patient
}
```

### 4. Access Control

- Implement role-based access control (RBAC) on every endpoint
- Roles: `case_manager`, `case_manager_assistant`, `physician`, `admin`, `system_agent`
- Case managers should only see patients on their caseload
- Agents operate under a `system_agent` service account with scoped permissions
- All authentication via OAuth 2.0 / JWT with short-lived tokens (15 min access, 24hr refresh)
- Log all access events (who accessed what patient record, when)

```python
# Every API endpoint must check authorization
@require_role(["case_manager", "admin"])
@require_patient_access(patient_id)  # verify this user is assigned to this patient
def get_patient_workflow(patient_id: str):
    ...
```

### 5. Model I/O Safety

All inputs to and outputs from Granite models must pass through safety filters:

```python
async def safe_model_call(prompt: str, patient_context: dict) -> str:
    # 1. Filter PHI from prompt before logging
    sanitized_prompt = phi_filter.redact(prompt)
    audit_log.log_model_input(sanitized_prompt)

    # 2. Call model
    response = await watsonx_ai.generate(
        model="granite-4-h-small",
        prompt=prompt  # actual prompt with PHI goes to model (model is within BAA boundary)
    )

    # 3. Filter output before logging
    sanitized_output = phi_filter.redact(response.text)
    audit_log.log_model_output(sanitized_output)

    # 4. Check for hallucination / safety via Granite Guardian
    safety_check = await granite_guardian.evaluate(response.text, patient_context)
    if not safety_check.passed:
        audit_log.log_safety_flag(safety_check.reason)
        raise SafetyException(safety_check.reason)

    return response.text
```

### 6. Data at Rest

- All database tables containing PHI must use column-level encryption (AES-256)
- Encryption keys managed via IBM Key Protect (FIPS 140-2 Level 4 HSMs) or equivalent KMS
- Database backups are encrypted
- Encryption key rotation: minimum annually, immediately on suspected compromise

```python
# Schema example — encrypted columns marked
class Patient(Base):
    __tablename__ = "patients"
    id = Column(String, primary_key=True)                    # internal UUID, not MRN
    epic_patient_id_encrypted = Column(EncryptedString)      # FHIR Patient ID — encrypted
    name_encrypted = Column(EncryptedString)                 # patient name — encrypted
    dob_encrypted = Column(EncryptedString)                  # date of birth — encrypted
    coverage_payer_id = Column(String)                       # payer ID — not PHI alone
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

### 7. Data in Transit

- All API endpoints: HTTPS only (TLS 1.3), reject HTTP
- FHIR API calls to Epic: TLS 1.3 with certificate pinning
- Availity API calls: TLS 1.3
- Internal service-to-service: mTLS (mutual TLS)
- WebSocket connections (if used for real-time updates): WSS only

### 8. De-identification for Training & Analytics

If any patient data is used for model fine-tuning, analytics, or reporting:
- Apply Safe Harbor method (remove all 18 HIPAA identifiers) OR Expert Determination method
- Never use production PHI in development or staging environments
- Synthetic data generators must produce realistic but non-identifiable records

### 9. Business Associate Agreement (BAA)

Every third-party service that processes, stores, or transmits PHI requires a BAA:
- IBM Cloud — BAA required (available for HIPAA-eligible services, Dallas region)
- Epic — covered under existing hospital vendor agreement
- Availity — BAA required
- WellSky/CarePort — BAA required
- Any monitoring/logging service — must be HIPAA-eligible or receive only de-identified data

### 10. Incident Response

If a PHI breach is detected or suspected:
1. Log the incident immediately with timestamp, scope, and affected records
2. Do NOT attempt to cover up or silently fix — HIPAA requires breach notification
3. Notify the security/compliance team (in production: hospital's privacy officer)
4. Preserve all relevant logs and evidence
5. In code: throw a `BreachDetectedException` that triggers the incident workflow

---

## CMS-0057-F Regulatory Compliance

The CMS Interoperability and Prior Authorization Final Rule (CMS-0057-F) mandates that by January 2027, all Medicare Advantage, Medicaid, and marketplace payers must:

1. **Prior Authorization API** — Accept electronic PA submissions via FHIR (Da Vinci PAS IG)
2. **Documentation Requirements** — Support automated documentation retrieval (Da Vinci DTR IG)
3. **Coverage Requirements Discovery** — Expose whether PA is required for a given service (Da Vinci CRD IG)
4. **Status tracking** — Provide real-time PA decision status via API
5. **72-hour response** — Respond to non-urgent PA requests within 7 calendar days (down from no mandated timeline)

**Implementation guidance:**
- Build the Availity integration to support BOTH X12 278 (current) and FHIR PAS (future)
- Use a strategy/adapter pattern so swapping between submission methods is a config change, not a code change
- Log which submission method was used for each PA request in the audit trail

---

## Development Rules

### Testing
- Use synthetic patient data only — never real PHI, not even "anonymized" production data
- Provide a synthetic data generator: `scripts/generate_synthetic_patients.py`
- FHIR sandbox: use Epic's open sandbox (https://fhir.epic.com/) for integration testing
- Availity sandbox: use Availity's developer sandbox for PA submission testing

### Environment Separation
- Development, staging, and production are fully isolated
- No PHI in development or staging — synthetic data only
- Production credentials are never committed to version control
- Use environment variables for all secrets (see product design doc Section 9)

### Code Review Checklist (HIPAA-specific)
Before merging any PR, verify:
- [ ] No raw PHI in log statements, comments, or error messages
- [ ] All new database columns containing PHI are encrypted
- [ ] All new API endpoints have RBAC decorators
- [ ] All new model calls go through `safe_model_call` wrapper
- [ ] Audit logging added for any new agent action touching patient data
- [ ] No PHI in URL paths or query parameters
- [ ] Synthetic data used in all test fixtures
- [ ] No new third-party services added without BAA confirmation

### Dependencies
- Only use HIPAA-eligible cloud services
- Pin all dependency versions — no floating ranges
- Run `npm audit` / `pip audit` before every release
- No client-side analytics libraries (Google Analytics, Mixpanel, etc.) unless HIPAA-eligible and under BAA

---

## Tech Stack Quick Reference

| Layer | Technology |
|-------|-----------|
| Frontend | React + @carbon/react (IBM Carbon v11) |
| API | Python (FastAPI) |
| Agent Framework | BeeAI Framework |
| LLM | IBM Granite 4.0 via watsonx.ai API |
| Database | PostgreSQL with column-level encryption |
| Cache | Redis (HIPAA-eligible deployment) |
| Auth | OAuth 2.0 / SMART on FHIR |
| EHR Integration | Epic FHIR R4 APIs |
| Payer Integration | Availity (X12 278 + Da Vinci PAS) |
| Referrals | WellSky/CarePort API |
| Governance | watsonx.governance |
| Infrastructure | IBM Cloud (Dallas) or OpenShift |
| CI/CD | GitHub Actions (no PHI in pipeline) |

---

## File Structure

```
dischargeiq/
├── CLAUDE.md                          # THIS FILE
├── docs/
│   ├── DischargeIQ_Product_Design_Doc.md
│   └── DischargeIQ_Frontend_Design_Principles.md
├── src/
│   ├── agents/
│   │   ├── supervisor.py
│   │   ├── prior_auth.py
│   │   ├── placement.py
│   │   └── compliance.py
│   ├── api/
│   │   ├── routes/
│   │   ├── middleware/
│   │   │   ├── auth.py            # RBAC + JWT validation
│   │   │   └── phi_filter.py      # PHI redaction middleware
│   │   └── main.py
│   ├── integrations/
│   │   ├── epic_fhir.py           # SMART on FHIR client
│   │   ├── availity.py            # X12 278 + FHIR PAS adapter
│   │   ├── careport.py            # WellSky/CarePort client
│   │   └── watsonx.py             # watsonx.ai + governance client
│   ├── models/                     # SQLAlchemy / data models
│   ├── security/
│   │   ├── encryption.py          # AES-256 column encryption
│   │   ├── hashing.py             # SHA-256 for audit logs
│   │   └── phi_redactor.py        # PII/PHI detection + redaction
│   └── frontend/                   # React + Carbon
│       └── (see Frontend Design Principles doc)
├── scripts/
│   └── generate_synthetic_patients.py
├── tests/
│   ├── fixtures/                   # Synthetic data only
│   └── ...
└── .env.example                    # Template — no real secrets
```
