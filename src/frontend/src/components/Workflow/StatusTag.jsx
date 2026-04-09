import React from 'react';
import { Tag } from '@carbon/react';
import { getStatusTagProps, STATUS_COLORS } from '../../utils/statusMapping';

export default function StatusTag({ status }) {
  const { type, label } = getStatusTagProps(status);

  // Special handling for AUTH_PENDING to show yellow background
  const customStyle =
    status === 'AUTH_PENDING'
      ? { backgroundColor: '#f1c21b', color: '#161616' }
      : {};

  return (
    <Tag type={type} style={customStyle}>
      {label}
    </Tag>
  );
}
