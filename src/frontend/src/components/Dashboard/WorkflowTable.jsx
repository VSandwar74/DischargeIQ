import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  DataTable,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell,
  TableToolbar,
  TableToolbarSearch,
  TableToolbarContent,
  TableContainer,
  OverflowMenu,
  OverflowMenuItem,
} from '@carbon/react';
import StatusTag from '../Workflow/StatusTag';

function relativeTime(isoString) {
  if (!isoString) return '\u2014';
  const now = new Date('2026-04-09T12:00:00Z');
  const then = new Date(isoString);
  const diffMs = now - then;
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHrs = Math.floor(diffMins / 60);
  if (diffHrs < 24) return `${diffHrs}h ago`;
  const diffDays = Math.floor(diffHrs / 24);
  return `${diffDays}d ago`;
}

const HEADERS = [
  { key: 'patient_name', header: 'Patient Name' },
  { key: 'patient_mrn', header: 'MRN' },
  { key: 'payer_name', header: 'Payer' },
  { key: 'status', header: 'Status' },
  { key: 'auth_submitted', header: 'Auth Submitted' },
  { key: 'facility_match', header: 'Facility Match' },
  { key: 'avoidable_days', header: 'Avoidable Days' },
  { key: 'actions', header: 'Actions' },
];

export default function WorkflowTable({ workflows = [] }) {
  const navigate = useNavigate();

  const rows = workflows.map((wf) => ({
    id: wf.id,
    patient_name: wf.patient_name,
    patient_mrn: wf.patient_mrn,
    payer_name: wf.payer_name,
    status: wf.status,
    auth_submitted: wf.prior_auth?.submitted_at || null,
    facility_match: wf.facility_matches?.length > 0
      ? wf.facility_matches.find((f) => f.referral_status === 'Accepted')?.facility_name
        || (wf.status === 'PLACEMENT_SEARCHING' ? 'Searching...' : wf.facility_matches[0]?.facility_name)
      : '\u2014',
    avoidable_days: wf.avoidable_days,
    patient_id: wf.patient_id,
  }));

  return (
    <DataTable rows={rows} headers={HEADERS} isSortable>
      {({
        rows: tableRows,
        headers,
        getHeaderProps,
        getRowProps,
        getTableProps,
        getTableContainerProps,
        onInputChange,
      }) => (
        <TableContainer
          title="Active Workflows"
          description="All discharge coordination workflows"
          {...getTableContainerProps()}
        >
          <TableToolbar>
            <TableToolbarContent>
              <TableToolbarSearch
                onChange={onInputChange}
                placeholder="Search patients..."
                persistent
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
                      if (cell.info.header === 'patient_name') {
                        return (
                          <TableCell key={cell.id}>
                            <span
                              className="semibold"
                              style={{ cursor: 'pointer', color: 'var(--cds-interactive)' }}
                              onClick={() => navigate(`/patients/${original?.patient_id}`)}
                              role="link"
                              tabIndex={0}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') navigate(`/patients/${original?.patient_id}`);
                              }}
                            >
                              {cell.value}
                            </span>
                          </TableCell>
                        );
                      }
                      if (cell.info.header === 'patient_mrn') {
                        return (
                          <TableCell key={cell.id}>
                            <span className="mono">{cell.value}</span>
                          </TableCell>
                        );
                      }
                      if (cell.info.header === 'status') {
                        return (
                          <TableCell key={cell.id}>
                            <StatusTag status={cell.value} />
                          </TableCell>
                        );
                      }
                      if (cell.info.header === 'auth_submitted') {
                        return (
                          <TableCell key={cell.id}>
                            {relativeTime(cell.value)}
                          </TableCell>
                        );
                      }
                      if (cell.info.header === 'avoidable_days') {
                        return (
                          <TableCell key={cell.id}>
                            <span className={cell.value > 2 ? 'avoidable-days--high' : ''}>
                              {cell.value}
                            </span>
                          </TableCell>
                        );
                      }
                      if (cell.info.header === 'actions') {
                        return (
                          <TableCell key={cell.id}>
                            <OverflowMenu flipped size="sm" ariaLabel="Actions">
                              <OverflowMenuItem
                                itemText="View Details"
                                onClick={() => navigate(`/patients/${original?.patient_id}`)}
                              />
                              <OverflowMenuItem
                                itemText="Escalate"
                                isDelete
                                onClick={() => {
                                  /* handled by parent */
                                }}
                              />
                            </OverflowMenu>
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
  );
}
