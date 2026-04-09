const STATUS_MAP = {
  INITIATED: { type: 'blue', label: 'Initiated' },
  AUTH_PENDING: { type: 'warm-gray', label: 'Auth Pending' },
  AUTH_APPROVED: { type: 'green', label: 'Auth Approved' },
  AUTH_DENIED: { type: 'red', label: 'Auth Denied' },
  PLACEMENT_SEARCHING: { type: 'teal', label: 'Searching' },
  PLACEMENT_CONFIRMED: { type: 'green', label: 'Placed' },
  TRANSPORT_SCHEDULED: { type: 'blue', label: 'Transport Scheduled' },
  DISCHARGED: { type: 'gray', label: 'Discharged' },
  ESCALATED: { type: 'purple', label: 'Escalated' },
};

export function getStatusTagProps(status) {
  return STATUS_MAP[status] || { type: 'gray', label: status || 'Unknown' };
}

export const STATUS_COLORS = {
  INITIATED: '#0f62fe',
  AUTH_PENDING: '#f1c21b',
  AUTH_APPROVED: '#24a148',
  AUTH_DENIED: '#da1e28',
  PLACEMENT_SEARCHING: '#009d9a',
  PLACEMENT_CONFIRMED: '#24a148',
  TRANSPORT_SCHEDULED: '#0f62fe',
  DISCHARGED: '#8d8d8d',
  ESCALATED: '#8a3ffc',
};

export default STATUS_MAP;
