import React, { useState, useEffect } from 'react';
import {
  DataTable,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell,
  TableContainer,
  TableToolbar,
  TableToolbarContent,
  Dropdown,
  Loading,
} from '@carbon/react';
import AGENT_COLORS from '../utils/agentColors';
import { fetchAuditLog } from '../utils/api';

const HEADERS = [
  { key: 'timestamp', header: 'Timestamp' },
  { key: 'agent', header: 'Agent' },
  { key: 'action', header: 'Action' },
  { key: 'status', header: 'Status' },
  { key: 'patient_id_hash', header: 'Patient ID (Hashed)' },
  { key: 'details', header: 'Details' },
  { key: 'session_id', header: 'Session ID' },
];

const AGENT_FILTER_OPTIONS = [
  { id: 'all', text: 'All Agents' },
  { id: 'supervisor', text: 'Supervisor' },
  { id: 'prior_auth', text: 'Prior Auth' },
  { id: 'placement', text: 'Placement' },
  { id: 'compliance', text: 'Compliance' },
];

function formatTimestamp(isoString) {
  if (!isoString) return '\u2014';
  return new Date(isoString).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  });
}

export default function AuditLogPage() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [agentFilter, setAgentFilter] = useState('all');

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const data = await fetchAuditLog();
        setEntries(data);
      } catch (err) {
        // Fallback handled in api.js
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const filtered = agentFilter === 'all'
    ? entries
    : entries.filter((e) => e.agent === agentFilter);

  const rows = filtered.map((entry) => ({
    id: entry.id,
    timestamp: entry.timestamp,
    agent: entry.agent,
    action: entry.action,
    status: entry.status,
    patient_id_hash: entry.patient_id_hash,
    details: entry.details,
    session_id: entry.session_id,
  }));

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '80px 0' }}>
        <Loading description="Loading audit log..." withOverlay={false} />
      </div>
    );
  }

  return (
    <div>
      <div className="audit-header">
        <div className="audit-header__title">Compliance Audit Trail</div>
        <div className="audit-header__subtitle">
          HIPAA-compliant audit log &mdash; patient identifiers are SHA-256 hashed
        </div>
      </div>

      <DataTable rows={rows} headers={HEADERS}>
        {({
          rows: tableRows,
          headers,
          getHeaderProps,
          getRowProps,
          getTableProps,
          getTableContainerProps,
        }) => (
          <TableContainer {...getTableContainerProps()}>
            <TableToolbar>
              <TableToolbarContent>
                <Dropdown
                  id="agent-filter"
                  titleText=""
                  label="Filter by agent"
                  items={AGENT_FILTER_OPTIONS}
                  itemToString={(item) => item?.text || ''}
                  selectedItem={AGENT_FILTER_OPTIONS.find((o) => o.id === agentFilter)}
                  onChange={({ selectedItem }) => setAgentFilter(selectedItem?.id || 'all')}
                  size="sm"
                  style={{ minWidth: '180px' }}
                />
              </TableToolbarContent>
            </TableToolbar>
            <Table {...getTableProps()} size="lg">
              <TableHead>
                <TableRow>
                  {headers.map((header) => (
                    <TableHeader key={header.key} {...getHeaderProps({ header })}>
                      {header.header}
                    </TableHeader>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {tableRows.map((row) => {
                  const original = rows.find((r) => r.id === row.id);
                  return (
                    <TableRow key={row.id} {...getRowProps({ row })}>
                      {row.cells.map((cell) => {
                        if (cell.info.header === 'timestamp') {
                          return (
                            <TableCell key={cell.id}>
                              <span className="mono" style={{ fontSize: '13px' }}>
                                {formatTimestamp(cell.value)}
                              </span>
                            </TableCell>
                          );
                        }
                        if (cell.info.header === 'agent') {
                          const color = AGENT_COLORS[cell.value] || '#8d8d8d';
                          return (
                            <TableCell key={cell.id}>
                              <span className={`agent-badge agent-badge--${cell.value}`}>
                                {cell.value?.replace('_', ' ')}
                              </span>
                            </TableCell>
                          );
                        }
                        if (cell.info.header === 'status') {
                          const isSuccess = cell.value === 'success';
                          return (
                            <TableCell key={cell.id}>
                              <span style={{
                                color: isSuccess ? '#24a148' : '#da1e28',
                                fontWeight: 500,
                                fontSize: '13px',
                              }}>
                                {cell.value}
                              </span>
                            </TableCell>
                          );
                        }
                        if (cell.info.header === 'patient_id_hash') {
                          const hash = cell.value || '';
                          return (
                            <TableCell key={cell.id}>
                              <span className="mono" style={{ fontSize: '13px' }}>
                                {hash.length > 12 ? hash.substring(0, 12) + '...' : hash}
                              </span>
                            </TableCell>
                          );
                        }
                        if (cell.info.header === 'session_id') {
                          return (
                            <TableCell key={cell.id}>
                              <span className="mono" style={{ fontSize: '13px' }}>
                                {cell.value}
                              </span>
                            </TableCell>
                          );
                        }
                        return <TableCell key={cell.id}>{cell.value}</TableCell>;
                      })}
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </DataTable>
    </div>
  );
}
