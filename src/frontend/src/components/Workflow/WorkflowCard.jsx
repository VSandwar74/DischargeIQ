import React from 'react';
import { Tile, Button } from '@carbon/react';
import { View, WarningAlt } from '@carbon/icons-react';
import StatusTag from './StatusTag';
import AGENT_COLORS from '../../utils/agentColors';

function computeLOS(createdAt) {
  const created = new Date(createdAt);
  const now = new Date('2026-04-09T12:00:00Z');
  return Math.ceil((now - created) / (1000 * 60 * 60 * 24));
}

function AgentDot({ agent, status }) {
  const color = AGENT_COLORS[agent] || '#8d8d8d';
  const isActive = status === 'active';
  return (
    <span
      className="workflow-card__agent-dot"
      style={{
        backgroundColor: isActive ? color : 'transparent',
        border: isActive ? 'none' : `2px solid ${color}`,
        display: 'inline-block',
      }}
      title={`${agent.replace('_', ' ')} - ${status}`}
    />
  );
}

export default function WorkflowCard({ workflow, onViewDetails, onEscalate }) {
  if (!workflow) return null;

  const los = computeLOS(workflow.created_at);

  // Determine agent statuses based on workflow
  const priorAuthActive = ['AUTH_PENDING', 'AUTH_DENIED', 'AUTH_APPROVED'].includes(workflow.status);
  const placementActive = ['PLACEMENT_SEARCHING', 'PLACEMENT_CONFIRMED', 'TRANSPORT_SCHEDULED'].includes(workflow.status);
  const complianceActive = workflow.audit_trail?.some((e) => e.agent === 'compliance');

  return (
    <Tile className="workflow-card" style={{ marginBottom: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span className="semibold" style={{ fontSize: '16px' }}>{workflow.patient_name}</span>
        <StatusTag status={workflow.status} />
      </div>

      <div className="workflow-card__meta">
        <span className="mono">{workflow.patient_mrn}</span>
        <span>{workflow.payer_name}</span>
        <span>{los} days</span>
      </div>

      <div className="workflow-card__agents">
        <AgentDot agent="prior_auth" status={priorAuthActive ? 'active' : 'inactive'} />
        <AgentDot agent="placement" status={placementActive ? 'active' : 'inactive'} />
        <AgentDot agent="compliance" status={complianceActive ? 'active' : 'inactive'} />
        <span style={{ fontSize: '11px', color: '#525252', marginLeft: '4px' }}>Agent Status</span>
      </div>

      <div style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
        <Button kind="primary" size="sm" renderIcon={View} onClick={onViewDetails}>
          View Details
        </Button>
        {workflow.status !== 'DISCHARGED' && workflow.status !== 'ESCALATED' && (
          <Button kind="ghost" size="sm" renderIcon={WarningAlt} onClick={onEscalate}>
            Escalate
          </Button>
        )}
      </div>
    </Tile>
  );
}
