import React from 'react';
import AGENT_COLORS from '../../utils/agentColors';

function formatTimestamp(isoString) {
  if (!isoString) return '';
  const d = new Date(isoString);
  return d.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

export default function AgentTimeline({ entries = [] }) {
  if (entries.length === 0) {
    return (
      <div style={{ color: 'var(--cds-text-secondary)', fontSize: '14px', padding: '12px 0' }}>
        No activity recorded yet.
      </div>
    );
  }

  const sorted = [...entries].sort(
    (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
  );

  return (
    <div style={{ paddingLeft: '4px' }}>
      {sorted.map((entry, idx) => {
        const isLast = idx === sorted.length - 1;
        const color = AGENT_COLORS[entry.agent] || '#8d8d8d';
        const isPending = entry.action?.includes('pending') || entry.action?.includes('searching');

        return (
          <div key={entry.id || idx} className="timeline-entry">
            {/* Dot */}
            <div style={{ position: 'relative' }}>
              <div
                className={`timeline-dot ${isPending ? 'pending' : ''}`}
                style={!isPending ? { backgroundColor: color } : { borderColor: color }}
              />
              {!isLast && <div className="timeline-line" />}
            </div>

            {/* Content */}
            <div className="timeline-content">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
                <div>
                  <div style={{ fontSize: '14px', fontWeight: 500, color: '#161616' }}>
                    {entry.action}
                  </div>
                  {entry.details && (
                    <div style={{ fontSize: '13px', color: '#525252', marginTop: '2px' }}>
                      {entry.details.split(/(ATN-\d+-\d+|UHC-\d+-\d+|CIG-\d+-\d+|HUM-\d+-\d+)/g).map(
                        (part, i) =>
                          /^(ATN|UHC|CIG|HUM)-\d+-\d+$/.test(part) ? (
                            <span key={i} className="mono" style={{ fontWeight: 500 }}>
                              {part}
                            </span>
                          ) : (
                            <span key={i}>{part}</span>
                          )
                      )}
                    </div>
                  )}
                  <div style={{ marginTop: '4px' }}>
                    <span
                      className="agent-badge"
                      style={{ backgroundColor: color }}
                    >
                      {entry.agent?.replace('_', ' ')}
                    </span>
                  </div>
                </div>
                <div className="timeline-time">{formatTimestamp(entry.timestamp)}</div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
