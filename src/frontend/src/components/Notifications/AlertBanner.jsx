import React, { useState } from 'react';
import { InlineNotification } from '@carbon/react';

const LEVEL_TO_KIND = {
  URGENT: 'error',
  WARNING: 'warning',
  INFO: 'info',
  SUCCESS: 'success',
};

export default function AlertBanner({ alerts = [] }) {
  const [dismissed, setDismissed] = useState(new Set());

  if (alerts.length === 0) return null;

  const visibleAlerts = alerts.filter((a) => !dismissed.has(a.id));
  if (visibleAlerts.length === 0) return null;

  return (
    <div style={{ marginBottom: '16px' }}>
      {visibleAlerts.map((alert) => {
        const kind = LEVEL_TO_KIND[alert.level] || 'info';
        const isUrgent = alert.level === 'URGENT';

        return (
          <InlineNotification
            key={alert.id}
            kind={kind}
            title={alert.title}
            subtitle={alert.message}
            hideCloseButton={false}
            lowContrast
            onClose={() => {
              setDismissed((prev) => new Set([...prev, alert.id]));
              return false;
            }}
            style={{ marginBottom: '8px' }}
          />
        );
      })}
    </div>
  );
}
