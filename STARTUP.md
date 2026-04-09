# DischargeIQ — Startup & Integration Guide

This document covers every external system you need access to for a full production deployment with live hospital integrations. For local demo/development, **none of these are required** — set `DEV_MODE=true` and the app runs entirely on synthetic data.

---

## Quick Start (Demo Mode — No External Access Needed)

```bash
# Backend
cp .env.example .env          # defaults to DEV_MODE=true
pip install -r requirements.txt
uvicorn src.api.main:app --reload

# Frontend
cd src/frontend && npm install && npm start
```

That's it. Everything uses mock clients with synthetic data.

---

## Production Mode Checklist

Set `DEV_MODE=false` in `.env` and configure the systems below.

| # | System | What It Does | Lead Time | Cost |
|---|--------|-------------|-----------|------|
| 1 | IBM watsonx.ai | LLM inference (Granite models) | 2–4 weeks | Pay-per-token |
| 2 | IBM watsonx.governance | Model safety, audit, bias detection | Included with watsonx | Included |
| 3 | Epic FHIR R4 | Patient data from the EHR | 3–12 months | Per hospital contract |
| 4 | Availity | Prior auth submission & status | 2–6 weeks (sandbox) | Per transaction |
| 5 | WellSky CarePort | SNF facility search & referrals | 1–3 months | Per hospital contract |
| 6 | PostgreSQL | Workflow & audit persistence | Immediate | Free (self-hosted) |
| 7 | Redis | Caching & rate limiting | Immediate | Free (self-hosted) |

---

## 1. IBM watsonx.ai

**Purpose:** Clinical text generation — appeal narratives, PA summaries, therapy score interpretation.

**Models used:**
- `ibm/granite-4-h-small` — primary clinical reasoning
- `ibm/granite-4-h-tiny` — high-volume payer rule matching
- `ibm/granite-guardian-3-8b` — safety checks (hallucination, PHI leakage)

**How to get access:**
1. Create an IBM Cloud account at [cloud.ibm.com](https://cloud.ibm.com)
2. Provision a **watsonx.ai** instance in the **Dallas (us-south)** region (required for HIPAA eligibility)
3. Create a project and note your **Project ID**
4. Generate an **API Key** under IAM → API Keys
5. (Optional) Provision **watsonx.governance** (OpenScale) for model monitoring

**Environment variables:**
```
WATSONX_API_KEY=<your-ibm-cloud-api-key>
WATSONX_PROJECT_ID=<your-project-id>
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_GOVERNANCE_URL=https://us-south.aiopenscale.cloud.ibm.com
```

**BAA:** Required. Contact IBM sales to execute a HIPAA BAA before sending any PHI. Only Dallas-region HIPAA-eligible services are covered.

**Auth flow:** API Key → IBM IAM token (`POST https://iam.cloud.ibm.com/identity/token`) → Bearer token on inference calls. Token auto-refreshes.

---

## 2. Epic FHIR R4

**Purpose:** Patient demographics, encounters, diagnoses, therapy assessments (AM-PAC scores), insurance coverage, clinical documents.

**FHIR resources accessed:**
| Resource | Data | FHIR Scope |
|----------|------|------------|
| Patient | Name, DOB, MRN, address | `patient/Patient.read` |
| Encounter | Admit date, inpatient vs observation status | `patient/Encounter.read` |
| Coverage | Payer, plan type (MA vs traditional Medicare) | `patient/Coverage.read` |
| Condition | ICD-10 diagnosis codes | `patient/Condition.read` |
| Observation | AM-PAC functional mobility scores | `patient/Observation.read` |
| DocumentReference | H&P, therapy notes, discharge summaries | `patient/DocumentReference.read` |

**How to get access:**

### Sandbox (free, immediate)
1. Sign up at [open.epic.com](https://open.epic.com/)
2. Register a **Backend Systems** app (non-patient-facing)
3. Use the public sandbox FHIR endpoint: `https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4`
4. Generate an RSA key pair and upload the public key to your app registration
5. Set environment variables pointing to sandbox

### Production (requires hospital partnership)
1. Enroll in Epic's **Vendor Services** program
2. Hospital IT must approve and provision your app in their Epic instance
3. Complete Epic's security review and connection agreement
4. Hospital provides their FHIR base URL and token endpoint

**Environment variables:**
```
EPIC_FHIR_BASE_URL=https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4
EPIC_CLIENT_ID=<your-smart-client-id>
EPIC_PRIVATE_KEY_PATH=/path/to/epic-private-key.pem
EPIC_TOKEN_ENDPOINT=https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token
```

**Auth flow:** Signed JWT assertion (RS384, 5-min expiry) → `POST` to token endpoint → 15-min access token. No refresh tokens — re-assert when expired.

**BAA:** Not separately required — covered under the hospital's existing Epic vendor agreement.

**Lead time:** Sandbox is instant. Production varies: 3–12 months depending on hospital IT timelines.

---

## 3. Availity

**Purpose:** Prior authorization submission, status tracking, payer rules discovery. Connects to 3M+ providers and processes 13B transactions/year.

**APIs used:**
| Endpoint | Purpose | Standard |
|----------|---------|----------|
| `POST /crd/coverage-requirements` | Check if PA is required for payer + SNF | Da Vinci CRD |
| `POST /dtr/populate-form` | Auto-fill PA form from clinical data | Da Vinci DTR |
| `POST /prior-authorizations` | Submit PA via X12 278 (current) | X12 278/275 |
| `POST /pas/submit` | Submit PA via FHIR PAS (future) | Da Vinci PAS |
| `GET /prior-authorizations/{id}` | Poll PA decision status | X12 278 |
| `GET /payers/{id}/capabilities` | Check if payer supports FHIR PAS | Custom |

**How to get access:**
1. Register at [developer.availity.com](https://developer.availity.com/)
2. Request **sandbox credentials** (Client ID + Client Secret)
3. Test PA submission workflows against sandbox payers
4. For production: your hospital must have an Availity subscription

**Environment variables:**
```
AVAILITY_API_BASE=https://api.availity.com/availity/v1
AVAILITY_CLIENT_ID=<your-client-id>
AVAILITY_CLIENT_SECRET=<your-client-secret>
```

**Auth flow:** OAuth 2.0 client_credentials grant → Bearer token.

**BAA:** Required. Standard Availity BAA covers all HIPAA-covered entities.

**CMS-0057-F note:** The code uses a strategy pattern — X12 278 today, FHIR PAS when payers adopt it (mandatory January 2027). Switching is a config change, not a code change.

---

## 4. WellSky CarePort

**Purpose:** SNF facility search (130K+ post-acute providers), electronic referral submission, bed availability, referral status tracking.

**APIs used:**
| Endpoint | Purpose |
|----------|---------|
| `POST /facilities/search` | Find SNFs by payer, distance, care capabilities, beds |
| `POST /referrals` | Send referral packet to a facility |
| `GET /referrals/{id}` | Track referral acceptance/decline |

**How to get access:**
1. Contact WellSky sales — CarePort is an enterprise product
2. Your hospital must be a CarePort customer (listed in Epic Toolbox)
3. Request API credentials (API Key + Hospital ID)
4. CarePort will provision your hospital in their referral network

**Environment variables:**
```
CAREPORT_API_BASE=https://api.careport.com/v2
CAREPORT_API_KEY=<your-api-key>
CAREPORT_HOSPITAL_ID=<your-hospital-npi-or-id>
```

**Auth flow:** API key in `X-API-Key` header + hospital context in `X-Hospital-ID` header. No OAuth — straightforward key-based auth.

**BAA:** Required. Standard WellSky BAA.

**Fallback:** If CarePort API is unavailable, the placement agent can generate referral packets for manual fax/email submission.

---

## 5. PostgreSQL

**Purpose:** Persistent storage for workflows, prior auth records, facility matches, and HIPAA audit trail (6-year retention).

**How to set up:**

### Local (development)
```bash
# macOS
brew install postgresql@16 && brew services start postgresql@16
createdb dischargeiq

# Or use Docker
docker run -d --name dischargeiq-db \
  -e POSTGRES_DB=dischargeiq \
  -e POSTGRES_USER=dischargeiq \
  -e POSTGRES_PASSWORD=<password> \
  -p 5432:5432 \
  postgres:16
```

### Run migrations
```bash
alembic upgrade head
```

### Production (HIPAA-eligible)
Use one of:
- **IBM Cloud Databases for PostgreSQL** (Dallas region, HIPAA-eligible)
- **AWS RDS for PostgreSQL** (with BAA)
- **Azure Database for PostgreSQL** (with BAA)

**Environment variables:**
```
DATABASE_URL=postgresql+asyncpg://dischargeiq:<password>@localhost:5432/dischargeiq
```

**BAA:** Required if using a cloud-managed database. Self-hosted on HIPAA-compliant infrastructure is also acceptable.

**Schema:** 5 tables — `patients`, `discharge_workflows`, `prior_auth_records`, `facility_matches`, `audit_entries`. PHI columns are encrypted at the application layer (Fernet AES-256).

---

## 6. Redis

**Purpose:** Session caching, PA status polling cache, rate limiting.

**How to set up:**

```bash
# macOS
brew install redis && brew services start redis

# Or Docker
docker run -d --name dischargeiq-redis -p 6379:6379 redis:7-alpine
```

**Environment variables:**
```
REDIS_URL=redis://localhost:6379/0
```

**BAA:** Required if caching PHI in a cloud-managed Redis instance. Use TLS-enabled Redis with encryption at rest.

---

## Security & Encryption Keys

Generate these before first run:

```bash
# Fernet encryption key (AES-256 for PHI at rest)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Audit salt (SHA-256 hashing for patient IDs in audit logs)
python -c "import secrets; print(secrets.token_hex(32))"

# JWT secret (API authentication)
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

```
ENCRYPTION_KEY=<fernet-key>
AUDIT_SALT=<random-hex-salt>
JWT_SECRET=<random-secret>
```

---

## BAA Summary

| System | BAA Required | Who Signs |
|--------|-------------|-----------|
| IBM watsonx | Yes | Hospital + IBM |
| Epic FHIR | No (covered by existing agreement) | — |
| Availity | Yes | Hospital + Availity |
| WellSky CarePort | Yes | Hospital + WellSky |
| PostgreSQL (cloud) | Yes | Hospital + cloud provider |
| Redis (cloud) | Yes | Hospital + cloud provider |

All BAAs must be executed **before** any PHI flows through the system.

---

## Recommended Setup Order

1. **IBM watsonx** — fastest to provision, enables LLM features immediately
2. **PostgreSQL + Redis** — local setup is instant, enables persistence
3. **Availity sandbox** — 2–6 week approval, unblocks PA workflow testing
4. **Epic FHIR sandbox** — instant for public sandbox, enables clinical data testing
5. **WellSky CarePort** — longest lead time, start the sales conversation early

---

## Architecture Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  React UI   │────▶│  FastAPI      │────▶│  PostgreSQL     │
│  (Carbon)   │     │  Backend      │     │  (workflows,    │
└─────────────┘     │               │     │   audit trail)  │
                    │  Agents:      │     └─────────────────┘
                    │  ┌──────────┐ │
                    │  │Supervisor│ │────▶ Epic FHIR R4
                    │  │PA Agent  │ │────▶ Availity (PA)
                    │  │Placement │ │────▶ CarePort (SNF)
                    │  │Compliance│ │────▶ watsonx.ai (LLM)
                    │  └──────────┘ │────▶ watsonx.governance
                    └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │    Redis     │
                    │  (cache)     │
                    └──────────────┘
```

---

## Switching from Demo to Production

```bash
# 1. Fill in all credentials in .env
# 2. Flip the switch
DEV_MODE=false

# 3. Run database migrations
alembic upgrade head

# 4. Start the server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

The factory functions in each integration file (`create_epic_client()`, `create_availity_client()`, etc.) automatically return the live client when `DEV_MODE=false`. No code changes needed.
