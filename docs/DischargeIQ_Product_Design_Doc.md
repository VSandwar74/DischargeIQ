# DischargeIQ — Product Design Document

**Version:** 1.0 | **Date:** April 2026 | **Status:** MVP Specification
**Team:** Yellow Team (Alex, Fanny, Vishakh, Tejas) | NYU Stern × IBM watsonx AI Labs

---

## 1. Problem Statement

Hospital "bed blocking" — patients medically cleared for discharge but unable to leave due to administrative delays — costs U.S. hospitals an estimated $35B+ annually. The primary bottleneck is **insurance prior authorization for post-acute (skilled nursing facility) placements**, which takes 1–5 days per patient. Secondary delays include post-acute facility matching and family coordination.

**Core insight from primary research:** Case managers juggle 20–22 patients, have portal access for only 3 of dozens of Medicare Advantage payers (Aetna Medicare, UnitedHealthcare Medicare, Anthem Advantage), and lose all visibility when other payers require the receiving facility to submit authorization. One interviewee reported waiting Wednesday → Monday for a single Aetna Medicare authorization — by which time the patient could have gone home.

**What DischargeIQ does:** An agentic AI system that automates prior authorization submission, tracks approval status, coordinates SNF placement, and maintains HIPAA-compliant audit trails — built on IBM watsonx.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    DISCHARGEIQ SYSTEM                        │
│                                                             │
│  ┌───────────────┐   ┌──────────────────┐   ┌────────────┐ │
│  │  Supervisor    │   │  Prior Auth      │   │ Placement  │ │
│  │  Agent         │──▶│  Agent           │   │ Coordinator│ │
│  │  (Orchestrate) │   │  (Granite 4.0)   │   │ Agent      │ │
│  │                │──▶│                  │   │            │ │
│  │                │   └──────────────────┘   └────────────┘ │
│  │                │   ┌──────────────────┐                  │
│  │                │──▶│  Compliance &    │                  │
│  │                │   │  Governance Agent│                  │
│  └───────────────┘   └──────────────────┘                  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  INTEGRATION LAYER                                          │
│  Epic FHIR R4 APIs ←→ Availity (X12 278/275 + FHIR PAS)   │
│  WellSky/CarePort (SNF referrals) ←→ watsonx.data          │
├─────────────────────────────────────────────────────────────┤
│  GOVERNANCE LAYER                                           │
│  watsonx.governance: audit trails, PII filters, drift,     │
│  explainability, HIPAA compliance, model monitoring         │
└─────────────────────────────────────────────────────────────┘
```

### Platform Stack

| Layer | Component | Purpose |
|-------|-----------|---------|
| Orchestration | **watsonx Orchestrate** | Multi-agent coordination (sequential/parallel/hierarchical), human-in-the-loop checkpoints, Agent Development Kit (Python) |
| Inference | **watsonx.ai + Granite 4.0** | Clinical NLP, document extraction, form pre-population, appeal drafting |
| Data | **watsonx.data** | Open lakehouse (Apache Iceberg) for payer rules, historical auth patterns, clinical guidelines |
| Governance | **watsonx.governance** | HIPAA audit trails, bias/drift detection, PII filtering, AI Factsheets, compliance automation |
| Infrastructure | **IBM Cloud (Dallas region)** or **Red Hat OpenShift** on AWS/Azure | HIPAA-eligible services, BAA, FIPS 140-2 Level 4 HSMs |

---

## 3. Agent Specifications

### 3.1 Supervisor Agent

**Role:** Workflow orchestrator. Receives discharge-planning triggers from Epic, decomposes into subtasks, delegates to specialist agents, handles escalation.

**Implementation:**
- Framework: BeeAI Agent Framework (Apache 2.0, Python)
- Model: Granite-4.0-H-Small (32B total, 9B active params) — hybrid Mamba-2/Transformer, strong instruction-following, 70%+ GPU RAM reduction vs comparable models
- Pattern: Hierarchical orchestration via watsonx Orchestrate
- Protocols: MCP (Model Context Protocol) and A2A (Agent-to-Agent)

**Trigger conditions:**
1. New discharge order detected in Epic (via FHIR Subscription or CDS Hooks)
2. Therapy assessment completed (AMPAC score available)
3. Case manager manually initiates workflow

**Workflow logic (pseudocode):**
```python
async def handle_discharge_trigger(patient_id: str, trigger: TriggerEvent):
    # 1. Extract clinical context
    patient_data = await epic_fhir.get_patient_bundle(patient_id)
    therapy_notes = await epic_fhir.get_therapy_assessments(patient_id)
    insurance_info = await epic_fhir.get_coverage(patient_id)

    # 2. Determine if prior auth is needed
    pa_required = await prior_auth_agent.check_if_required(
        payer_id=insurance_info.payer_id,
        service_type="SNF",
        clinical_data=therapy_notes
    )

    # 3. Parallel execution: auth + placement
    if pa_required:
        auth_task = prior_auth_agent.submit(patient_data, insurance_info)
        placement_task = placement_agent.find_matches(patient_data)
        auth_result, placement_options = await asyncio.gather(auth_task, placement_task)
    else:
        placement_options = await placement_agent.find_matches(patient_data)
        auth_result = AuthResult(status="NOT_REQUIRED")

    # 4. Human-in-the-loop: present options to case manager
    await notify_case_manager(
        patient_id=patient_id,
        auth_status=auth_result,
        placement_options=placement_options
    )

    # 5. Compliance logging
    await compliance_agent.log_workflow(
        patient_id=patient_id,
        actions_taken=[auth_task, placement_task],
        outcome=auth_result
    )
```

### 3.2 Prior Authorization Agent

**Role:** Extracts clinical data from Epic, populates payer-specific authorization forms, submits via Availity, tracks status, drafts appeals on denial.

**Model:** Granite-4.0-H-Tiny (7B total, 1B active) for high-volume payer rules matching; Granite-4.0-H-Small for appeal narrative generation.

**Integration points:**

1. **Epic FHIR R4 APIs (read):**
   - `GET /Patient/{id}` — demographics
   - `GET /Encounter/{id}` — admission details, status (inpatient vs observation)
   - `GET /Condition?patient={id}` — diagnoses (ICD-10)
   - `GET /Observation?patient={id}&category=functional-status` — therapy scores (AMPAC)
   - `GET /DocumentReference?patient={id}` — H&P, therapy notes, clinical summaries
   - `GET /Coverage?patient={id}` — insurance details, MA plan info

2. **Availity (submit):**
   - **Legacy path:** X12 278 (authorization request) + 275 (additional info attachment)
   - **CMS-0057-F path (by Jan 2027):** Da Vinci PAS (Prior Authorization Support) FHIR IG
     - `POST [payer-base]/Claim/$submit` — FHIR-based PA submission
     - `GET [payer-base]/Claim/{id}` — real-time status polling
   - **Da Vinci CRD** (Coverage Requirements Discovery): real-time check at point of order whether PA is required
   - **Da Vinci DTR** (Documentation Templates & Rules): auto-populate payer questionnaires from EHR data

**Key logic:**
```python
class PriorAuthAgent:
    async def check_if_required(self, payer_id, service_type, clinical_data):
        """Da Vinci CRD: check if this payer requires PA for SNF placement"""
        crd_response = await availity.crd_check(payer_id, service_type)
        return crd_response.pa_required

    async def submit(self, patient_data, insurance_info):
        """Extract clinical docs, populate forms, submit via Availity"""
        # 1. Extract relevant clinical data using Granite
        clinical_summary = await self.extract_clinical_summary(patient_data)
        therapy_scores = self.get_ampac_scores(patient_data)

        # 2. Auto-populate payer form via DTR
        form_data = await availity.dtr_populate(
            payer_id=insurance_info.payer_id,
            clinical_summary=clinical_summary,
            therapy_scores=therapy_scores
        )

        # 3. Submit via PAS (FHIR) or X12 278 (legacy)
        if insurance_info.payer_supports_fhir:
            result = await availity.pas_submit(form_data)
        else:
            result = await availity.x12_278_submit(form_data)

        # 4. Start status polling
        self.start_polling(result.tracking_id, interval_minutes=30)
        return result

    async def draft_appeal(self, denial, patient_data):
        """On denial, use Granite to draft appeal with supporting clinical evidence"""
        prompt = f"""Draft a prior authorization appeal for SNF placement.
        Denial reason: {denial.reason}
        Patient clinical summary: {patient_data.clinical_summary}
        Therapy scores: {patient_data.ampac_score}
        Include: relevant clinical guidelines, functional status evidence,
        medical necessity justification."""
        return await watsonx_ai.generate(model="granite-4-h-small", prompt=prompt)
```

### 3.3 Placement Coordinator Agent

**Role:** Queries SNF bed availability, matches patient acuity to facilities, manages family preferences, coordinates logistics.

**Integration:**
- **WellSky/CarePort Community Referral Network** — listed in Epic Toolbox, connects 2,000+ hospitals with 130,000+ post-acute providers, 54M referrals/year, ~15 min average response time
- Referrals initiated from within Epic Case Management via CarePort APIs

**Key logic:**
```python
class PlacementAgent:
    async def find_matches(self, patient_data):
        """Query CarePort for available SNFs matching patient needs"""
        # 1. Build referral criteria
        criteria = {
            "care_needs": self.extract_care_needs(patient_data),  # PT, OT, wound care, IV abx, etc.
            "insurance": patient_data.coverage.payer_id,
            "location_preferences": patient_data.family_preferences.geography,
            "acuity_level": patient_data.therapy_scores.ampac_score,
            "behavioral_flags": patient_data.behavioral_assessment
        }

        # 2. Query CarePort for available facilities
        facilities = await careport.search_facilities(criteria)

        # 3. Rank by match quality (Granite inference)
        ranked = await self.rank_facilities(facilities, criteria)

        # 4. Filter out facilities that don't accept patient's insurance
        filtered = [f for f in ranked if patient_data.coverage.payer_id in f.accepted_payers]

        return filtered

    async def send_referral(self, patient_data, facility_id):
        """Send electronic referral via CarePort"""
        referral_packet = await self.build_referral_packet(patient_data)
        return await careport.send_referral(facility_id, referral_packet)
```

### 3.4 Compliance & Governance Agent

**Role:** Maintains HIPAA audit trails, enforces access controls, monitors model performance, ensures CMS-0057-F compliance.

**Implementation:**
- watsonx.governance AI Factsheets for full lifecycle tracking
- Real-time PII/PHI filters on all model inputs and outputs
- Prompt injection detection and hallucination monitoring for clinical contexts
- Role-based access control (RBAC) enforced at the agent level
- 6-year audit log retention (HIPAA requirement)

**Key capabilities:**
```python
class ComplianceAgent:
    async def log_workflow(self, patient_id, actions_taken, outcome):
        """Log every agent action to watsonx.governance"""
        await watsonx_governance.log_event({
            "patient_id_hash": self.hash_phi(patient_id),  # never log raw PHI
            "timestamp": datetime.utcnow(),
            "actions": [a.to_audit_record() for a in actions_taken],
            "outcome": outcome.status,
            "model_versions": self.get_active_model_versions(),
            "explainability": self.generate_decision_rationale(actions_taken)
        })

    async def check_observation_status(self, patient_data):
        """Flag if patient is observation status — no Medicare SNF benefit"""
        if patient_data.encounter.status == "observation":
            if patient_data.coverage.type == "medicare_ffs":
                return Alert(
                    level="CRITICAL",
                    message="Patient is observation status with traditional Medicare. "
                            "SNF placement will be private pay unless converted to inpatient. "
                            "Notify case manager and utilization review team."
                )
        return None
```

---

## 4. Data Model

### Core Entities

```typescript
interface Patient {
  id: string;                    // Epic FHIR Patient ID
  demographics: Demographics;
  encounters: Encounter[];       // Current + historical
  coverage: Coverage[];          // Insurance plans
  conditions: Condition[];       // Active diagnoses (ICD-10)
  therapyAssessments: TherapyAssessment[];  // AMPAC scores
  functionalStatus: FunctionalStatus;
  behavioralFlags: BehavioralFlag[];
}

interface DischargeWorkflow {
  id: string;
  patientId: string;
  status: "INITIATED" | "AUTH_PENDING" | "AUTH_APPROVED" | "AUTH_DENIED"
        | "PLACEMENT_SEARCHING" | "PLACEMENT_CONFIRMED" | "TRANSPORT_SCHEDULED"
        | "DISCHARGED" | "ESCALATED";
  triggerEvent: TriggerEvent;
  priorAuth: PriorAuthRecord | null;
  placementOptions: FacilityMatch[];
  selectedFacility: string | null;
  familyConsent: ConsentRecord | null;
  transportDetails: TransportRecord | null;
  auditTrail: AuditEntry[];
  avoidableDays: number;         // Tracked for hospital reporting
  createdAt: Date;
  updatedAt: Date;
}

interface PriorAuthRecord {
  id: string;
  payerId: string;
  payerName: string;
  submissionMethod: "FHIR_PAS" | "X12_278" | "PORTAL_MANUAL";
  status: "SUBMITTED" | "PENDING_REVIEW" | "APPROVED" | "DENIED" | "APPEAL_SUBMITTED";
  trackingNumber: string;
  submittedAt: Date;
  responseAt: Date | null;
  denialReason: string | null;
  appealDraft: string | null;
  clinicalDocsSent: string[];    // DocumentReference IDs
}

interface FacilityMatch {
  facilityId: string;
  facilityName: string;
  careportReferralId: string;
  bedAvailable: boolean;
  acceptsInsurance: boolean;
  matchScore: number;            // 0-100 based on acuity, location, care needs
  distance: number;              // miles from patient preference
  referralStatus: "SENT" | "ACCEPTED" | "DECLINED" | "NO_RESPONSE";
  declineReason: string | null;  // age, acuity, behavioral, insurance, capacity
}
```

---

## 5. Integration Specifications

### 5.1 Epic FHIR R4

- **Auth:** SMART on FHIR (OAuth 2.0) — backend services flow (client_credentials)
- **Subscription:** FHIR Subscription or CDS Hooks for real-time discharge order triggers
- **Scope:** `patient/*.read`, `encounter/*.read`, `coverage/*.read`, `condition/*.read`, `observation/*.read`, `documentreference/*.read`
- **Rate limits:** Epic enforces per-app rate limits; plan for 100 req/min baseline
- **Approval:** Requires Epic Vendor Services program enrollment (3–12 month lead time); plan to use Epic's App Orchard for distribution
- **Write-back:** For MVP, write-back is optional — case manager confirms actions in Epic manually. Post-MVP, use Epic's `Task` and `ServiceRequest` resources for write-back.

### 5.2 Availity

- **Network:** 3M+ connected providers, 13B annual transactions
- **Legacy:** X12 278 (PA request), 275 (clinical attachment), 270/271 (eligibility check)
- **FHIR (CMS-0057-F):** Da Vinci PAS, CRD, DTR — mandatory for all MA payers by Jan 2027
- **Auth:** OAuth 2.0 via Availity Developer Portal
- **Key payers accessible:** Aetna, UnitedHealthcare, Anthem, Humana, Cigna + regional MA plans

### 5.3 WellSky/CarePort

- **Integration:** Epic Toolbox listed; referrals initiated from Epic Case Management
- **API:** RESTful API for referral submission, status tracking, facility search
- **Coverage:** 2,000+ hospitals, 130,000+ post-acute providers, 54M referrals/year

---

## 6. MVP Scope

### In Scope (Phase 1 — 90-day pilot)

| Feature | Agent | Priority |
|---------|-------|----------|
| Extract clinical data from Epic FHIR for PA submission | Prior Auth | P0 |
| Auto-populate PA forms via Availity (X12 278 initially, FHIR PAS when available) | Prior Auth | P0 |
| Real-time PA status tracking with case manager alerts | Prior Auth | P0 |
| HIPAA audit trail for all agent actions | Compliance | P0 |
| Observation status detection and alerting | Compliance | P0 |
| SNF bed availability search via CarePort | Placement | P1 |
| Patient-facility matching (insurance, acuity, geography) | Placement | P1 |
| Appeal draft generation on PA denial | Prior Auth | P1 |
| Workflow dashboard for case managers | Supervisor | P1 |

### Out of Scope (Phase 1)

- Transport scheduling and logistics
- Family communication / patient portal
- Non-MA insurance types (Medicaid, commercial)
- Non-SNF post-acute settings (home health, LTACH, IRF)
- Write-back to Epic (case manager confirms manually)
- Multi-hospital orchestration

### Target Environment

- **Hospitals:** 3–5 high-occupancy urban academic medical centers
- **Geography:** High-MA-penetration states (NY, FL, CA)
- **EHR:** Epic (38% US market share)
- **Success metric:** Reduce average discharge delay by ≥30% within 90-day pilot
- **Secondary metrics:** PA submission-to-approval time, case manager time saved per discharge, avoidable bed-days eliminated

---

## 7. Security & Compliance

| Requirement | Implementation |
|-------------|---------------|
| HIPAA BAA | IBM Cloud HIPAA-eligible services (Dallas region) |
| PHI encryption at rest | AES-256 via IBM Key Protect, FIPS 140-2 Level 4 HSMs |
| PHI encryption in transit | TLS 1.3 |
| Access control | RBAC via IBM IAM; minimum necessary principle |
| Audit logging | watsonx.governance + IBM Cloud Activity Tracker; 6-year retention |
| PII/PHI filtering | watsonx.governance real-time filters on all model I/O |
| De-identification | Required for any training data; Safe Harbor or Expert Determination method |
| Model monitoring | watsonx.governance: drift, bias, fairness metrics, hallucination detection |
| CMS-0057-F | Da Vinci IG compliance for PA interoperability (mandatory Jan 2027) |

---

## 8. Development Roadmap

### Phase 0: Foundation (Weeks 1–4)
- Set up IBM Cloud environment with HIPAA BAA
- Deploy watsonx.ai with Granite 4.0 models
- Establish Epic FHIR sandbox access (Epic's open sandbox for development)
- Build Availity developer sandbox integration
- Implement core data models and audit logging

### Phase 1: Prior Auth Agent (Weeks 5–10)
- FHIR data extraction pipeline (patient, encounter, coverage, clinical docs)
- Granite-powered clinical summarization for PA form population
- Availity X12 278 submission and status polling
- Denial detection and appeal draft generation
- Case manager notification system

### Phase 2: Placement Coordinator (Weeks 8–12)
- CarePort API integration for facility search
- Patient-facility matching algorithm
- Referral submission and tracking
- Insurance-based facility filtering

### Phase 3: Integration & Pilot (Weeks 10–14)
- Supervisor agent orchestration (watsonx Orchestrate)
- End-to-end workflow testing
- Case manager dashboard (web UI)
- Pilot deployment at 1–2 hospitals
- Performance measurement against baseline

---

## 9. Environment Variables & Configuration

```env
# IBM watsonx
WATSONX_API_KEY=<ibm-cloud-api-key>
WATSONX_PROJECT_ID=<project-id>
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_MODEL_PRIMARY=ibm/granite-4-h-small
WATSONX_MODEL_FAST=ibm/granite-4-h-tiny
WATSONX_GOVERNANCE_URL=<governance-endpoint>

# Epic FHIR
EPIC_FHIR_BASE_URL=https://<epic-instance>/api/FHIR/R4
EPIC_CLIENT_ID=<smart-on-fhir-client-id>
EPIC_PRIVATE_KEY_PATH=./keys/epic_jwk.pem
EPIC_TOKEN_ENDPOINT=https://<epic-instance>/oauth2/token

# Availity
AVAILITY_API_BASE=https://api.availity.com/availity/v1
AVAILITY_CLIENT_ID=<availity-client-id>
AVAILITY_CLIENT_SECRET=<availity-secret>

# CarePort / WellSky
CAREPORT_API_BASE=https://api.careport.com/v2
CAREPORT_API_KEY=<careport-key>
CAREPORT_HOSPITAL_ID=<facility-npi>

# Application
DATABASE_URL=postgresql://<connection-string>
REDIS_URL=redis://<connection-string>
LOG_LEVEL=INFO
AUDIT_RETENTION_YEARS=6
```

---

## 10. Key Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Epic vendor approval takes 3–12 months | High | Start with Epic open sandbox; pursue App Orchard listing in parallel; use read-only FHIR initially |
| Payer FHIR endpoints not ready before Jan 2027 | Medium | MVP uses X12 278 via Availity; FHIR PAS is future path |
| CarePort API access requires commercial agreement | Medium | WellSky partnership conversation; fallback to manual referral with agent-assisted packet generation |
| Granite clinical accuracy insufficient | Medium | Fine-tune via InstructLab on healthcare workflows; Granite Guardian 3.0 for safety guardrails; human-in-the-loop for all clinical decisions |
| Hospital IT resistance to new integrations | Medium | Read-only FHIR (no write-back in MVP); deploy on hospital's existing OpenShift if preferred |
| IBM has no current US hospital clients post-Watson Health divestiture | High | Position as greenfield opportunity; leverage IBM's enterprise sales team for health system CIO relationships; partner with Epic implementation firms |

---

## 11. Pricing Model

**Hybrid performance-aligned:**
- **Base fee:** $5K–$10K/month per hospital (covers infrastructure, support)
- **Gain-share:** 15–20% of revenue recaptured from reduced avoidable bed-days
- **Target ACV:** $300K per hospital / $750K per IDN (Integrated Delivery Network)
- **Rationale:** Eliminates budget objections from cash-strapped hospitals; aligns vendor incentive with hospital financial outcome

---

## 12. Instructions for Claude Code

When building the MVP, prioritize in this order:

1. **Start with the data layer:** Stand up the PostgreSQL schema for `DischargeWorkflow`, `PriorAuthRecord`, `FacilityMatch`, and `AuditEntry`. Every agent action must be logged.

2. **Build the Epic FHIR client first:** Use the Epic open sandbox (https://fhir.epic.com/). Implement the SMART on FHIR backend services auth flow, then build extractors for Patient, Encounter, Coverage, Condition, Observation (functional status), and DocumentReference.

3. **Build the Prior Auth Agent as Agent #1:** This is the highest-value agent. Clinical data extraction → form population → Availity submission → status polling → case manager alerting. Use Granite-4.0-H-Small via watsonx.ai API for clinical summarization.

4. **Use BeeAI Framework for agent orchestration:** `pip install beeai-framework`. Configure with `LLM_BACKEND=watsonx`. Each agent runs as a separate BeeAI agent with defined tools.

5. **Build a minimal case manager dashboard:** React frontend showing workflow status per patient: auth status, placement options, alerts. This is the human-in-the-loop surface.

6. **Compliance is not optional:** Every model call must be logged with input/output, model version, timestamp, and patient context (hashed). Use watsonx.governance APIs from day one.

7. **For the demo/pilot:** If full Availity integration isn't feasible in the timeline, build a mock payer endpoint that simulates the X12 278 request/response cycle with realistic latencies and approval/denial rates. The architecture should be identical — just swap the endpoint.

---

*This document synthesizes the team's research, primary interviews with hospital case managers, IBM watsonx technical documentation, and competitive analysis conducted February–April 2026.*
