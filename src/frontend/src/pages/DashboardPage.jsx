import React, { useState, useEffect } from 'react';
import { Grid, Column, Loading } from '@carbon/react';
import SummaryCards from '../components/Dashboard/SummaryCards';
import WorkflowTable from '../components/Dashboard/WorkflowTable';
import AlertBanner from '../components/Notifications/AlertBanner';
import { fetchDashboardSummary, fetchAlerts, fetchWorkflows } from '../utils/api';

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [summaryData, alertsData, workflowsData] = await Promise.all([
          fetchDashboardSummary(),
          fetchAlerts(),
          fetchWorkflows(),
        ]);
        setSummary(summaryData);
        setAlerts(alertsData);
        setWorkflows(workflowsData);
      } catch (err) {
        // Fallbacks are handled inside each API function
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '80px 0' }}>
        <Loading description="Loading dashboard..." withOverlay={false} />
      </div>
    );
  }

  return (
    <div>
      <h2 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '24px' }}>
        Discharge Coordination Dashboard
      </h2>

      <AlertBanner alerts={alerts} />

      <div style={{ marginBottom: '24px' }}>
        <SummaryCards data={summary} />
      </div>

      <WorkflowTable workflows={workflows} />
    </div>
  );
}
