import React from 'react';
import { Badge } from 'react-bootstrap';
import { STATUS_COLORS, STATUS_ICONS } from '../../utils/constants';

export default function StatusBadge({ status, criticality }) {
  const normalizedStatus = status ? status.toUpperCase() : 'UNKNOWN';
  const variant = STATUS_COLORS[normalizedStatus] || 'secondary';
  const icon = STATUS_ICONS[normalizedStatus] || '❓';
  const isNonCritical = criticality === 'NON_CRITICAL';

  return (
    <span>
      <Badge bg={variant} className="px-2 py-1">
        <span className="me-1" aria-hidden="true">{icon}</span>
        {normalizedStatus}
      </Badge>
      {isNonCritical && (
        <Badge bg="light" text="muted" className="ms-1 px-2 py-1" style={{ fontSize: '0.7em', border: '1px solid #dee2e6' }}>
          Non-Critical
        </Badge>
      )}
    </span>
  );
}
