import React from 'react';
import { Grid, Column, Tile } from '@carbon/react';
import { ArrowUp, ArrowDown } from '@carbon/icons-react';

function DeltaIndicator({ value, invertColor = false }) {
  if (value == null) return null;
  const isPositive = value > 0;
  // For delay, positive delta is bad (more days). invertColor flips the logic.
  const isGood = invertColor ? !isPositive : isPositive;
  const Icon = isPositive ? ArrowUp : ArrowDown;
  const className = isGood
    ? 'summary-card__delta summary-card__delta--positive'
    : 'summary-card__delta summary-card__delta--negative';
  const sign = isPositive ? '+' : '';

  return (
    <span className={className}>
      <Icon size={16} />
      {sign}{value}
    </span>
  );
}

export default function SummaryCards({ data }) {
  if (!data) return null;

  const cards = [
    {
      label: 'Auth Pending',
      value: data.auth_pending_count,
      delta: data.auth_pending_delta,
      invertColor: true, // more pending = bad
    },
    {
      label: 'Placed Today',
      value: data.placed_today_count,
      delta: data.placed_delta,
      invertColor: false, // more placed = good
    },
    {
      label: 'Avg Delay (Days)',
      value: data.avg_delay_days,
      delta: data.delay_delta,
      invertColor: true, // positive delay delta = bad
    },
  ];

  return (
    <Grid narrow>
      <Column lg={16} md={8} sm={4}>
        <div className="summary-cards-row" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          {cards.map((card) => (
            <Tile key={card.label} className="summary-card">
              <div className="summary-card__label">{card.label}</div>
              <div className="summary-card__value">{card.value}</div>
              <DeltaIndicator value={card.delta} invertColor={card.invertColor} />
            </Tile>
          ))}
        </div>
      </Column>
    </Grid>
  );
}
