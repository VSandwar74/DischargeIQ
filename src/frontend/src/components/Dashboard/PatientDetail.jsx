import React from 'react';
import { Grid, Column, Button, Tag, ProgressBar } from '@carbon/react';
import { Checkmark, CloseFilled, InProgress } from '@carbon/icons-react';
import StatusTag from '../Workflow/StatusTag';
import AgentTimeline from '../Workflow/AgentTimeline';

function PriorAuthCard({ priorAuth }) {
  if (!priorAuth) return null;

  return (
    <div className="detail-card">
      <div className="detail-card__title">Prior Authorization</div>
      <div className="detail-row">
        <span className="detail-row__label">Tracking Number</span>
        <span className="detail-row__value mono">{priorAuth.tracking_number || '\u2014'}</span>
      </div>
      <div className="detail-row">
        <span className="detail-row__label">Status</span>
        <span className="detail-row__value">
          {priorAuth.status === 'APPROVED' && <Tag type="green">Approved</Tag>}
          {priorAuth.status === 'DENIED' && <Tag type="red">Denied</Tag>}
          {priorAuth.status === 'PENDING' && <Tag type="blue">Pending</Tag>}
          {priorAuth.status === 'NOT_STARTED' && <Tag type="gray">Not Started</Tag>}
        </span>
      </div>
      <div className="detail-row">
        <span className="detail-row__label">Payer</span>
        <span className="detail-row__value">{priorAuth.payer_name}</span>
      </div>
      <div className="detail-row">
        <span className="detail-row__label">Submission Method</span>
        <span className="detail-row__value">{priorAuth.submission_method || '\u2014'}</span>
      </div>
      <div className="detail-row">
        <span className="detail-row__label">Submitted</span>
        <span className="detail-row__value">
          {priorAuth.submitted_at
            ? new Date(priorAuth.submitted_at).toLocaleString()
            : '\u2014'}
        </span>
      </div>
      <div className="detail-row">
        <span className="detail-row__label">Response</span>
        <span className="detail-row__value">
          {priorAuth.response_at
            ? new Date(priorAuth.response_at).toLocaleString()
            : 'Awaiting response'}
        </span>
      </div>
      {priorAuth.denial_reason && (
        <div style={{ marginTop: '12px', padding: '12px', background: '#fff1f1', borderRadius: '4px' }}>
          <div style={{ fontSize: '12px', fontWeight: 600, color: '#da1e28', marginBottom: '4px' }}>
            Denial Reason
          </div>
          <div style={{ fontSize: '14px', color: '#161616' }}>{priorAuth.denial_reason}</div>
        </div>
      )}
      {priorAuth.appeal_draft && (
        <div style={{ marginTop: '12px', padding: '12px', background: '#f4f4f4', borderRadius: '4px' }}>
          <div style={{ fontSize: '12px', fontWeight: 600, color: '#525252', marginBottom: '4px' }}>
            Generated Appeal Draft
          </div>
          <div style={{ fontSize: '14px', color: '#161616', fontStyle: 'italic' }}>
            {priorAuth.appeal_draft}
          </div>
        </div>
      )}
    </div>
  );
}

function FacilityMatchesCard({ facilities }) {
  if (!facilities || facilities.length === 0) {
    return (
      <div className="detail-card">
        <div className="detail-card__title">Facility Matches</div>
        <div style={{ color: 'var(--cds-text-secondary)', fontSize: '14px' }}>
          No facilities matched yet.
        </div>
      </div>
    );
  }

  return (
    <div className="detail-card">
      <div className="detail-card__title">Facility Matches</div>
      {facilities.map((f, idx) => (
        <div key={idx} className="facility-match">
          <div className="facility-match__name">{f.facility_name}</div>
          <div style={{ margin: '8px 0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
              <span>Match Score</span>
              <span className="semibold">{f.match_score}%</span>
            </div>
            <div style={{ height: '4px', background: '#e0e0e0', borderRadius: '2px', overflow: 'hidden' }}>
              <div
                style={{
                  height: '100%',
                  width: `${f.match_score}%`,
                  background: f.match_score >= 90 ? '#24a148' : f.match_score >= 80 ? '#0f62fe' : '#f1c21b',
                  borderRadius: '2px',
                }}
              />
            </div>
          </div>
          <div className="facility-match__meta">
            <span>{f.distance_miles} mi</span>
            <span>{f.bed_available ? 'Bed Available' : 'No Beds'}</span>
            <span>{f.accepts_insurance ? 'Accepts Insurance' : 'Out of Network'}</span>
            <span>
              {f.referral_status === 'Accepted' && <Tag type="green" size="sm">Accepted</Tag>}
              {f.referral_status === 'Pending' && <Tag type="blue" size="sm">Pending</Tag>}
              {f.referral_status === 'On Hold' && <Tag type="warm-gray" size="sm">On Hold</Tag>}
              {f.referral_status === 'Not Sent' && <Tag type="gray" size="sm">Not Sent</Tag>}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

function computeLOS(createdAt) {
  const created = new Date(createdAt);
  const now = new Date('2026-04-09T12:00:00Z');
  return Math.ceil((now - created) / (1000 * 60 * 60 * 24));
}

export default function PatientDetail({ workflow, onApproveAuth, onSelectFacility, onEscalate }) {
  if (!workflow) return null;

  const los = computeLOS(workflow.created_at);

  return (
    <div>
      <div className="patient-header">
        <span className="patient-header__name">{workflow.patient_name}</span>
        <span className="patient-header__mrn">{workflow.patient_mrn}</span>
        <span className="patient-header__payer">{workflow.payer_name}</span>
        <StatusTag status={workflow.status} />
        <Tag type="outline">LOS: {los} days</Tag>
      </div>

      <Grid narrow>
        <Column lg={8} md={4} sm={4}>
          <div className="detail-card">
            <div className="detail-card__title">Agent Activity Timeline</div>
            <AgentTimeline entries={workflow.audit_trail || []} />
          </div>
        </Column>
        <Column lg={8} md={4} sm={4}>
          <PriorAuthCard priorAuth={workflow.prior_auth} />
          <FacilityMatchesCard facilities={workflow.facility_matches} />
        </Column>
      </Grid>

      <div className="actions-row">
        {workflow.prior_auth?.status === 'PENDING' && (
          <Button kind="primary" size="md" onClick={onApproveAuth}>
            Approve Auth
          </Button>
        )}
        {workflow.facility_matches?.some((f) => f.referral_status === 'Accepted') && (
          <Button kind="secondary" size="md" onClick={onSelectFacility}>
            Select Facility
          </Button>
        )}
        {workflow.status !== 'DISCHARGED' && workflow.status !== 'ESCALATED' && (
          <Button kind="danger--ghost" size="md" onClick={onEscalate}>
            Escalate
          </Button>
        )}
      </div>
    </div>
  );
}
