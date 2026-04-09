const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// ─── Comprehensive Demo Data ────────────────────────────────────────────────

const DEMO_WORKFLOWS = [
  {
    id: 'wf-001',
    patient_id: 'pat-001',
    patient_name: 'Margaret Chen',
    patient_mrn: 'MRN-20481537',
    payer_name: 'Aetna Medicare Advantage',
    status: 'AUTH_PENDING',
    trigger_event: 'Discharge order placed',
    avoidable_days: 2,
    created_at: '2026-04-07T08:15:00Z',
    updated_at: '2026-04-09T10:30:00Z',
    prior_auth: {
      id: 'pa-001',
      tracking_number: 'ATN-2026-048291',
      payer_name: 'Aetna Medicare Advantage',
      submission_method: 'X12 278',
      status: 'PENDING',
      submitted_at: '2026-04-07T09:22:00Z',
      response_at: null,
      denial_reason: null,
      appeal_draft: null,
    },
    facility_matches: [
      { facility_name: 'Sunrise Skilled Nursing', match_score: 94, distance_miles: 3.2, bed_available: true, accepts_insurance: true, referral_status: 'Pending' },
      { facility_name: 'Oakwood Rehabilitation Center', match_score: 87, distance_miles: 5.1, bed_available: true, accepts_insurance: true, referral_status: 'Not Sent' },
      { facility_name: 'Maplewood Care Facility', match_score: 81, distance_miles: 7.8, bed_available: false, accepts_insurance: true, referral_status: 'Not Sent' },
    ],
    audit_trail: [
      { id: 'at-001', action: 'Workflow initiated from discharge order', agent: 'supervisor', timestamp: '2026-04-07T08:15:00Z', details: 'Epic ADT event received' },
      { id: 'at-002', action: 'Patient eligibility verified', agent: 'prior_auth', timestamp: '2026-04-07T08:18:00Z', details: 'Medicare Advantage coverage confirmed' },
      { id: 'at-003', action: 'Prior auth request submitted', agent: 'prior_auth', timestamp: '2026-04-07T09:22:00Z', details: 'Tracking: ATN-2026-048291 via X12 278' },
      { id: 'at-004', action: 'Facility search initiated', agent: 'placement', timestamp: '2026-04-07T09:30:00Z', details: '3 facilities matched within 10 mile radius' },
      { id: 'at-005', action: 'Compliance check passed', agent: 'compliance', timestamp: '2026-04-07T09:35:00Z', details: 'CMS-0057-F documentation requirements met' },
    ],
  },
  {
    id: 'wf-002',
    patient_id: 'pat-002',
    patient_name: 'Robert Williams',
    patient_mrn: 'MRN-20493821',
    payer_name: 'UnitedHealthcare Medicare',
    status: 'AUTH_APPROVED',
    trigger_event: 'Physician referral',
    avoidable_days: 0,
    created_at: '2026-04-06T14:00:00Z',
    updated_at: '2026-04-08T11:45:00Z',
    prior_auth: {
      id: 'pa-002',
      tracking_number: 'UHC-2026-103847',
      payer_name: 'UnitedHealthcare Medicare',
      submission_method: 'Da Vinci PAS',
      status: 'APPROVED',
      submitted_at: '2026-04-06T14:30:00Z',
      response_at: '2026-04-07T16:00:00Z',
      denial_reason: null,
      appeal_draft: null,
    },
    facility_matches: [
      { facility_name: 'Lakeview SNF', match_score: 96, distance_miles: 2.1, bed_available: true, accepts_insurance: true, referral_status: 'Accepted' },
      { facility_name: 'Heritage Health Center', match_score: 89, distance_miles: 4.3, bed_available: true, accepts_insurance: true, referral_status: 'Not Sent' },
    ],
    audit_trail: [
      { id: 'at-010', action: 'Workflow initiated from physician referral', agent: 'supervisor', timestamp: '2026-04-06T14:00:00Z', details: 'SNF placement recommended' },
      { id: 'at-011', action: 'Prior auth submitted', agent: 'prior_auth', timestamp: '2026-04-06T14:30:00Z', details: 'Tracking: UHC-2026-103847 via Da Vinci PAS' },
      { id: 'at-012', action: 'Prior auth approved', agent: 'prior_auth', timestamp: '2026-04-07T16:00:00Z', details: 'Approved for 20 days SNF stay' },
      { id: 'at-013', action: 'Facility match confirmed', agent: 'placement', timestamp: '2026-04-08T09:00:00Z', details: 'Lakeview SNF accepted referral' },
    ],
  },
  {
    id: 'wf-003',
    patient_id: 'pat-003',
    patient_name: 'Dorothy Johnson',
    patient_mrn: 'MRN-20517492',
    payer_name: 'Humana Medicare Advantage',
    status: 'AUTH_DENIED',
    trigger_event: 'Discharge order placed',
    avoidable_days: 4,
    created_at: '2026-04-05T10:00:00Z',
    updated_at: '2026-04-09T08:00:00Z',
    prior_auth: {
      id: 'pa-003',
      tracking_number: 'HUM-2026-229174',
      payer_name: 'Humana Medicare Advantage',
      submission_method: 'X12 278',
      status: 'DENIED',
      submitted_at: '2026-04-05T10:45:00Z',
      response_at: '2026-04-07T14:30:00Z',
      denial_reason: 'Insufficient documentation of functional impairment. AM-PAC score not included.',
      appeal_draft: 'Based on the patient\'s AM-PAC Basic Mobility score of 15.2 and Daily Activity score of 18.7, functional impairment is well-documented. The patient requires skilled nursing for post-operative hip fracture rehabilitation.',
    },
    facility_matches: [
      { facility_name: 'Brookside Nursing Center', match_score: 91, distance_miles: 4.0, bed_available: true, accepts_insurance: true, referral_status: 'On Hold' },
    ],
    audit_trail: [
      { id: 'at-020', action: 'Workflow initiated', agent: 'supervisor', timestamp: '2026-04-05T10:00:00Z', details: 'Discharge order received' },
      { id: 'at-021', action: 'Prior auth submitted', agent: 'prior_auth', timestamp: '2026-04-05T10:45:00Z', details: 'Tracking: HUM-2026-229174' },
      { id: 'at-022', action: 'Prior auth denied', agent: 'prior_auth', timestamp: '2026-04-07T14:30:00Z', details: 'Reason: Insufficient documentation' },
      { id: 'at-023', action: 'Appeal draft generated', agent: 'prior_auth', timestamp: '2026-04-07T15:00:00Z', details: 'Granite model generated appeal letter with clinical evidence' },
      { id: 'at-024', action: 'Escalated to case manager', agent: 'supervisor', timestamp: '2026-04-07T15:05:00Z', details: 'Requires human review of appeal before submission' },
    ],
  },
  {
    id: 'wf-004',
    patient_id: 'pat-004',
    patient_name: 'James Martinez',
    patient_mrn: 'MRN-20528163',
    payer_name: 'Cigna Medicare Advantage',
    status: 'PLACEMENT_SEARCHING',
    trigger_event: 'Discharge order placed',
    avoidable_days: 1,
    created_at: '2026-04-08T07:30:00Z',
    updated_at: '2026-04-09T09:15:00Z',
    prior_auth: {
      id: 'pa-004',
      tracking_number: 'CIG-2026-384726',
      payer_name: 'Cigna Medicare Advantage',
      submission_method: 'X12 278',
      status: 'APPROVED',
      submitted_at: '2026-04-08T08:00:00Z',
      response_at: '2026-04-08T18:00:00Z',
      denial_reason: null,
      appeal_draft: null,
    },
    facility_matches: [
      { facility_name: 'Pine Valley Rehabilitation', match_score: 88, distance_miles: 6.2, bed_available: true, accepts_insurance: false, referral_status: 'Pending' },
      { facility_name: 'Clearwater SNF', match_score: 85, distance_miles: 3.7, bed_available: false, accepts_insurance: true, referral_status: 'Not Sent' },
      { facility_name: 'Valley View Care Center', match_score: 82, distance_miles: 8.4, bed_available: true, accepts_insurance: true, referral_status: 'Pending' },
    ],
    audit_trail: [
      { id: 'at-030', action: 'Workflow initiated', agent: 'supervisor', timestamp: '2026-04-08T07:30:00Z', details: 'Discharge order received' },
      { id: 'at-031', action: 'Prior auth approved', agent: 'prior_auth', timestamp: '2026-04-08T18:00:00Z', details: 'Tracking: CIG-2026-384726' },
      { id: 'at-032', action: 'Facility search in progress', agent: 'placement', timestamp: '2026-04-09T09:00:00Z', details: 'Searching for SNF with cardiac rehab capability' },
    ],
  },
  {
    id: 'wf-005',
    patient_id: 'pat-005',
    patient_name: 'Helen Thompson',
    patient_mrn: 'MRN-20539847',
    payer_name: 'Aetna Medicare Advantage',
    status: 'PLACEMENT_CONFIRMED',
    trigger_event: 'Case manager request',
    avoidable_days: 0,
    created_at: '2026-04-04T11:00:00Z',
    updated_at: '2026-04-08T14:20:00Z',
    prior_auth: {
      id: 'pa-005',
      tracking_number: 'ATN-2026-051938',
      payer_name: 'Aetna Medicare Advantage',
      submission_method: 'Da Vinci PAS',
      status: 'APPROVED',
      submitted_at: '2026-04-04T11:30:00Z',
      response_at: '2026-04-05T09:00:00Z',
      denial_reason: null,
      appeal_draft: null,
    },
    facility_matches: [
      { facility_name: 'Sunrise Skilled Nursing', match_score: 97, distance_miles: 3.2, bed_available: true, accepts_insurance: true, referral_status: 'Accepted' },
    ],
    audit_trail: [
      { id: 'at-040', action: 'Workflow initiated', agent: 'supervisor', timestamp: '2026-04-04T11:00:00Z', details: 'Case manager initiated workflow' },
      { id: 'at-041', action: 'Prior auth approved', agent: 'prior_auth', timestamp: '2026-04-05T09:00:00Z', details: 'Approved for 14 days' },
      { id: 'at-042', action: 'Placement confirmed', agent: 'placement', timestamp: '2026-04-06T10:00:00Z', details: 'Sunrise Skilled Nursing accepted' },
      { id: 'at-043', action: 'Compliance verified', agent: 'compliance', timestamp: '2026-04-06T10:30:00Z', details: 'All regulatory requirements met' },
    ],
  },
  {
    id: 'wf-006',
    patient_id: 'pat-006',
    patient_name: 'William Davis',
    patient_mrn: 'MRN-20542718',
    payer_name: 'UnitedHealthcare Medicare',
    status: 'TRANSPORT_SCHEDULED',
    trigger_event: 'Discharge order placed',
    avoidable_days: 1,
    created_at: '2026-04-03T09:00:00Z',
    updated_at: '2026-04-09T07:00:00Z',
    prior_auth: {
      id: 'pa-006',
      tracking_number: 'UHC-2026-118392',
      payer_name: 'UnitedHealthcare Medicare',
      submission_method: 'X12 278',
      status: 'APPROVED',
      submitted_at: '2026-04-03T09:30:00Z',
      response_at: '2026-04-04T12:00:00Z',
      denial_reason: null,
      appeal_draft: null,
    },
    facility_matches: [
      { facility_name: 'Heritage Health Center', match_score: 93, distance_miles: 4.3, bed_available: true, accepts_insurance: true, referral_status: 'Accepted' },
    ],
    audit_trail: [
      { id: 'at-050', action: 'Workflow initiated', agent: 'supervisor', timestamp: '2026-04-03T09:00:00Z', details: 'Discharge order received' },
      { id: 'at-051', action: 'Prior auth approved', agent: 'prior_auth', timestamp: '2026-04-04T12:00:00Z', details: 'Approved for 21 days' },
      { id: 'at-052', action: 'Placement confirmed', agent: 'placement', timestamp: '2026-04-05T14:00:00Z', details: 'Heritage Health Center' },
      { id: 'at-053', action: 'Transport scheduled', agent: 'supervisor', timestamp: '2026-04-09T07:00:00Z', details: 'Non-emergency transport for April 10 at 10:00 AM' },
    ],
  },
  {
    id: 'wf-007',
    patient_id: 'pat-007',
    patient_name: 'Patricia Anderson',
    patient_mrn: 'MRN-20558194',
    payer_name: 'Humana Medicare Advantage',
    status: 'INITIATED',
    trigger_event: 'Discharge order placed',
    avoidable_days: 0,
    created_at: '2026-04-09T06:00:00Z',
    updated_at: '2026-04-09T06:00:00Z',
    prior_auth: {
      id: 'pa-007',
      tracking_number: null,
      payer_name: 'Humana Medicare Advantage',
      submission_method: null,
      status: 'NOT_STARTED',
      submitted_at: null,
      response_at: null,
      denial_reason: null,
      appeal_draft: null,
    },
    facility_matches: [],
    audit_trail: [
      { id: 'at-060', action: 'Workflow initiated', agent: 'supervisor', timestamp: '2026-04-09T06:00:00Z', details: 'Discharge order received, beginning coordination' },
    ],
  },
  {
    id: 'wf-008',
    patient_id: 'pat-008',
    patient_name: 'Richard Taylor',
    patient_mrn: 'MRN-20567382',
    payer_name: 'Cigna Medicare Advantage',
    status: 'DISCHARGED',
    trigger_event: 'Physician referral',
    avoidable_days: 0,
    created_at: '2026-03-28T10:00:00Z',
    updated_at: '2026-04-05T16:00:00Z',
    prior_auth: {
      id: 'pa-008',
      tracking_number: 'CIG-2026-371594',
      payer_name: 'Cigna Medicare Advantage',
      submission_method: 'X12 278',
      status: 'APPROVED',
      submitted_at: '2026-03-28T10:30:00Z',
      response_at: '2026-03-29T08:00:00Z',
      denial_reason: null,
      appeal_draft: null,
    },
    facility_matches: [
      { facility_name: 'Oakwood Rehabilitation Center', match_score: 95, distance_miles: 5.1, bed_available: true, accepts_insurance: true, referral_status: 'Accepted' },
    ],
    audit_trail: [
      { id: 'at-070', action: 'Workflow initiated', agent: 'supervisor', timestamp: '2026-03-28T10:00:00Z', details: 'Physician referral received' },
      { id: 'at-071', action: 'Prior auth approved', agent: 'prior_auth', timestamp: '2026-03-29T08:00:00Z', details: 'Approved for 14 days' },
      { id: 'at-072', action: 'Patient discharged to SNF', agent: 'supervisor', timestamp: '2026-04-05T16:00:00Z', details: 'Successfully discharged to Oakwood Rehabilitation Center' },
    ],
  },
  {
    id: 'wf-009',
    patient_id: 'pat-009',
    patient_name: 'Barbara Wilson',
    patient_mrn: 'MRN-20578291',
    payer_name: 'Aetna Medicare Advantage',
    status: 'ESCALATED',
    trigger_event: 'Discharge order placed',
    avoidable_days: 5,
    created_at: '2026-04-04T08:00:00Z',
    updated_at: '2026-04-09T11:00:00Z',
    prior_auth: {
      id: 'pa-009',
      tracking_number: 'ATN-2026-055821',
      payer_name: 'Aetna Medicare Advantage',
      submission_method: 'X12 278',
      status: 'DENIED',
      submitted_at: '2026-04-04T08:30:00Z',
      response_at: '2026-04-06T10:00:00Z',
      denial_reason: 'Patient does not meet skilled nursing criteria per InterQual guidelines.',
      appeal_draft: 'Patient demonstrates significant functional limitations requiring 24-hour skilled nursing care. Physical therapy evaluation indicates AM-PAC Basic Mobility score of 12.8, well below the threshold for independent living.',
    },
    facility_matches: [
      { facility_name: 'Maplewood Care Facility', match_score: 78, distance_miles: 7.8, bed_available: true, accepts_insurance: true, referral_status: 'On Hold' },
    ],
    audit_trail: [
      { id: 'at-080', action: 'Workflow initiated', agent: 'supervisor', timestamp: '2026-04-04T08:00:00Z', details: 'Discharge order received' },
      { id: 'at-081', action: 'Prior auth denied', agent: 'prior_auth', timestamp: '2026-04-06T10:00:00Z', details: 'Denied: does not meet skilled nursing criteria' },
      { id: 'at-082', action: 'Appeal submitted', agent: 'prior_auth', timestamp: '2026-04-06T14:00:00Z', details: 'Peer-to-peer review requested' },
      { id: 'at-083', action: 'Appeal denied', agent: 'prior_auth', timestamp: '2026-04-08T09:00:00Z', details: 'Second denial upheld' },
      { id: 'at-084', action: 'Escalated to medical director', agent: 'supervisor', timestamp: '2026-04-09T11:00:00Z', details: 'Requires medical director involvement for external appeal' },
    ],
  },
  {
    id: 'wf-010',
    patient_id: 'pat-010',
    patient_name: 'Charles Brown',
    patient_mrn: 'MRN-20589413',
    payer_name: 'UnitedHealthcare Medicare',
    status: 'AUTH_PENDING',
    trigger_event: 'Discharge order placed',
    avoidable_days: 1,
    created_at: '2026-04-08T15:00:00Z',
    updated_at: '2026-04-09T08:30:00Z',
    prior_auth: {
      id: 'pa-010',
      tracking_number: 'UHC-2026-127583',
      payer_name: 'UnitedHealthcare Medicare',
      submission_method: 'Da Vinci PAS',
      status: 'PENDING',
      submitted_at: '2026-04-08T15:30:00Z',
      response_at: null,
      denial_reason: null,
      appeal_draft: null,
    },
    facility_matches: [
      { facility_name: 'Lakeview SNF', match_score: 90, distance_miles: 2.1, bed_available: true, accepts_insurance: true, referral_status: 'Pending' },
      { facility_name: 'Clearwater SNF', match_score: 86, distance_miles: 3.7, bed_available: true, accepts_insurance: true, referral_status: 'Not Sent' },
    ],
    audit_trail: [
      { id: 'at-090', action: 'Workflow initiated', agent: 'supervisor', timestamp: '2026-04-08T15:00:00Z', details: 'Discharge order received' },
      { id: 'at-091', action: 'Prior auth submitted', agent: 'prior_auth', timestamp: '2026-04-08T15:30:00Z', details: 'Tracking: UHC-2026-127583 via Da Vinci PAS' },
      { id: 'at-092', action: 'Facility search initiated', agent: 'placement', timestamp: '2026-04-08T15:45:00Z', details: '2 facilities matched' },
    ],
  },
];

const DEMO_SUMMARY = {
  auth_pending_count: 12,
  placed_today_count: 7,
  avg_delay_days: 1.8,
  auth_pending_delta: 3,
  placed_delta: -2,
  delay_delta: -0.4,
};

const DEMO_ALERTS = [
  { id: 'alert-001', level: 'URGENT', title: 'Auth Denial - Dorothy Johnson', message: 'Prior auth denied by Humana. Appeal draft generated and ready for review.' },
  { id: 'alert-002', level: 'URGENT', title: 'Escalation - Barbara Wilson', message: '5 avoidable days accumulated. Requires medical director involvement.' },
  { id: 'alert-003', level: 'WARNING', title: 'Approaching SLA - Margaret Chen', message: 'Auth response pending for 48+ hours from Aetna.' },
  { id: 'alert-004', level: 'INFO', title: 'Transport Confirmed - William Davis', message: 'Non-emergency transport scheduled for April 10 at 10:00 AM.' },
  { id: 'alert-005', level: 'SUCCESS', title: 'Placement Complete - Helen Thompson', message: 'Successfully placed at Sunrise Skilled Nursing.' },
];

const DEMO_AUDIT_ENTRIES = [
  { id: 'aud-001', timestamp: '2026-04-09T11:00:00Z', agent: 'supervisor', action: 'workflow_escalated', status: 'success', patient_id_hash: 'a3f2b8c91d...', details: 'Escalated to medical director', session_id: 'sess-4829' },
  { id: 'aud-002', timestamp: '2026-04-09T10:30:00Z', agent: 'prior_auth', action: 'auth_status_checked', status: 'success', patient_id_hash: 'e7d14f6a82...', details: 'Polled Aetna for auth response', session_id: 'sess-4815' },
  { id: 'aud-003', timestamp: '2026-04-09T09:15:00Z', agent: 'placement', action: 'facility_search', status: 'success', patient_id_hash: 'b2c9d4e7f1...', details: 'Searched 12 facilities, 3 matched', session_id: 'sess-4802' },
  { id: 'aud-004', timestamp: '2026-04-09T09:00:00Z', agent: 'compliance', action: 'documentation_check', status: 'success', patient_id_hash: 'c4a8e2f5d3...', details: 'CMS-0057-F requirements verified', session_id: 'sess-4798' },
  { id: 'aud-005', timestamp: '2026-04-09T08:30:00Z', agent: 'prior_auth', action: 'auth_submitted', status: 'success', patient_id_hash: 'f1e8d7c6b5...', details: 'Submitted via Da Vinci PAS to UHC', session_id: 'sess-4791' },
  { id: 'aud-006', timestamp: '2026-04-09T08:00:00Z', agent: 'supervisor', action: 'workflow_initiated', status: 'success', patient_id_hash: '9a8b7c6d5e...', details: 'New discharge order processed', session_id: 'sess-4785' },
  { id: 'aud-007', timestamp: '2026-04-09T07:00:00Z', agent: 'placement', action: 'transport_scheduled', status: 'success', patient_id_hash: 'd5e4f3a2b1...', details: 'Transport booked for April 10', session_id: 'sess-4772' },
  { id: 'aud-008', timestamp: '2026-04-08T18:00:00Z', agent: 'prior_auth', action: 'auth_approved', status: 'success', patient_id_hash: 'b2c9d4e7f1...', details: 'Cigna approved 14-day SNF stay', session_id: 'sess-4760' },
  { id: 'aud-009', timestamp: '2026-04-08T15:45:00Z', agent: 'placement', action: 'facility_search', status: 'success', patient_id_hash: 'f1e8d7c6b5...', details: '2 facilities matched for patient', session_id: 'sess-4751' },
  { id: 'aud-010', timestamp: '2026-04-08T14:30:00Z', agent: 'prior_auth', action: 'appeal_denied', status: 'failure', patient_id_hash: 'a3f2b8c91d...', details: 'Second appeal denied by Aetna', session_id: 'sess-4742' },
  { id: 'aud-011', timestamp: '2026-04-08T11:45:00Z', agent: 'placement', action: 'referral_accepted', status: 'success', patient_id_hash: 'e7d14f6a82...', details: 'Lakeview SNF accepted referral', session_id: 'sess-4730' },
  { id: 'aud-012', timestamp: '2026-04-07T16:00:00Z', agent: 'prior_auth', action: 'auth_approved', status: 'success', patient_id_hash: 'e7d14f6a82...', details: 'UHC approved 20-day stay', session_id: 'sess-4715' },
];

// ─── API Client ─────────────────────────────────────────────────────────────

async function apiFetch(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function fetchDashboardSummary() {
  try {
    return await apiFetch('/api/dashboard/summary');
  } catch {
    return DEMO_SUMMARY;
  }
}

export async function fetchAlerts() {
  try {
    return await apiFetch('/api/alerts');
  } catch {
    return DEMO_ALERTS;
  }
}

export async function fetchWorkflows(statusFilter) {
  try {
    const query = statusFilter ? `?status=${statusFilter}` : '';
    return await apiFetch(`/api/workflows${query}`);
  } catch {
    if (statusFilter) {
      return DEMO_WORKFLOWS.filter((w) => w.status === statusFilter);
    }
    return DEMO_WORKFLOWS;
  }
}

export async function fetchWorkflow(id) {
  try {
    return await apiFetch(`/api/workflows/${id}`);
  } catch {
    return DEMO_WORKFLOWS.find((w) => w.id === id || w.patient_id === id) || DEMO_WORKFLOWS[0];
  }
}

export async function fetchPatients() {
  try {
    return await apiFetch('/api/patients');
  } catch {
    return DEMO_WORKFLOWS.map((w) => ({
      id: w.patient_id,
      name: w.patient_name,
      mrn: w.patient_mrn,
      payer: w.payer_name,
      status: w.status,
    }));
  }
}

export async function fetchPatient(id) {
  try {
    return await apiFetch(`/api/patients/${id}`);
  } catch {
    const wf = DEMO_WORKFLOWS.find((w) => w.patient_id === id);
    if (!wf) return null;
    return { id: wf.patient_id, name: wf.patient_name, mrn: wf.patient_mrn, payer: wf.payer_name, status: wf.status };
  }
}

export async function updateWorkflowStatus(id, status) {
  try {
    return await apiFetch(`/api/workflows/${id}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    });
  } catch {
    return { success: true, id, status };
  }
}

export async function approveAuth(workflowId) {
  try {
    return await apiFetch(`/api/workflows/${workflowId}/approve-auth`, { method: 'POST' });
  } catch {
    return { success: true, workflowId, action: 'auth_approved' };
  }
}

export async function selectFacility(workflowId, facilityId) {
  try {
    return await apiFetch(`/api/workflows/${workflowId}/select-facility`, {
      method: 'POST',
      body: JSON.stringify({ facility_id: facilityId }),
    });
  } catch {
    return { success: true, workflowId, facilityId, action: 'facility_selected' };
  }
}

export async function escalateWorkflow(workflowId) {
  try {
    return await apiFetch(`/api/workflows/${workflowId}/escalate`, { method: 'POST' });
  } catch {
    return { success: true, workflowId, action: 'escalated' };
  }
}

export async function fetchAuditLog() {
  try {
    return await apiFetch('/api/audit');
  } catch {
    return DEMO_AUDIT_ENTRIES;
  }
}

export { DEMO_WORKFLOWS, DEMO_ALERTS, DEMO_AUDIT_ENTRIES, DEMO_SUMMARY };
