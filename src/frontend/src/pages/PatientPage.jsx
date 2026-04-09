import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Loading, Button } from '@carbon/react';
import { ArrowLeft } from '@carbon/icons-react';
import PatientDetail from '../components/Dashboard/PatientDetail';
import ConfirmAction from '../components/Modals/ConfirmAction';
import { fetchWorkflow, approveAuth, selectFacility, escalateWorkflow } from '../utils/api';

export default function PatientPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [workflow, setWorkflow] = useState(null);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState({ open: false, type: null });

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const data = await fetchWorkflow(id);
        setWorkflow(data);
      } catch (err) {
        // Fallback handled in api.js
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [id]);

  const handleConfirm = async () => {
    if (!workflow) return;

    try {
      switch (modal.type) {
        case 'approve_auth':
          await approveAuth(workflow.id);
          setWorkflow((prev) => ({
            ...prev,
            status: 'AUTH_APPROVED',
            prior_auth: { ...prev.prior_auth, status: 'APPROVED', response_at: new Date().toISOString() },
          }));
          break;
        case 'select_facility': {
          const accepted = workflow.facility_matches?.find((f) => f.referral_status === 'Accepted');
          if (accepted) {
            await selectFacility(workflow.id, accepted.facility_name);
            setWorkflow((prev) => ({ ...prev, status: 'PLACEMENT_CONFIRMED' }));
          }
          break;
        }
        case 'escalate':
          await escalateWorkflow(workflow.id);
          setWorkflow((prev) => ({ ...prev, status: 'ESCALATED' }));
          break;
        default:
          break;
      }
    } catch (err) {
      // Error handling
    } finally {
      setModal({ open: false, type: null });
    }
  };

  const MODAL_CONFIG = {
    approve_auth: {
      title: 'Approve Prior Authorization',
      description:
        'The prior auth agent will mark this authorization as approved and notify the placement agent to proceed with facility selection. This action will be recorded in the compliance audit trail.',
      isDanger: false,
    },
    select_facility: {
      title: 'Confirm Facility Selection',
      description:
        'The placement agent will confirm the selected facility and initiate referral acceptance. Transport coordination will begin automatically. This action will be recorded in the compliance audit trail.',
      isDanger: false,
    },
    escalate: {
      title: 'Escalate Workflow',
      description:
        'This will escalate the workflow to the medical director for review. The supervisor agent will halt automated actions and flag this case for immediate human intervention. This action will be recorded in the compliance audit trail.',
      isDanger: true,
    },
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '80px 0' }}>
        <Loading description="Loading patient data..." withOverlay={false} />
      </div>
    );
  }

  if (!workflow) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <p style={{ color: 'var(--cds-text-secondary)' }}>Patient not found.</p>
        <Button kind="ghost" renderIcon={ArrowLeft} onClick={() => navigate('/')}>
          Back to Dashboard
        </Button>
      </div>
    );
  }

  const currentModal = modal.type ? MODAL_CONFIG[modal.type] : {};

  return (
    <div>
      <Button
        kind="ghost"
        size="sm"
        renderIcon={ArrowLeft}
        onClick={() => navigate('/')}
        style={{ marginBottom: '16px' }}
      >
        Back to Dashboard
      </Button>

      <PatientDetail
        workflow={workflow}
        onApproveAuth={() => setModal({ open: true, type: 'approve_auth' })}
        onSelectFacility={() => setModal({ open: true, type: 'select_facility' })}
        onEscalate={() => setModal({ open: true, type: 'escalate' })}
      />

      <ConfirmAction
        open={modal.open}
        title={currentModal.title || ''}
        description={currentModal.description || ''}
        isDanger={currentModal.isDanger || false}
        onConfirm={handleConfirm}
        onClose={() => setModal({ open: false, type: null })}
      />
    </div>
  );
}
