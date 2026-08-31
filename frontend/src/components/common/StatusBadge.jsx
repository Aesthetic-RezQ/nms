import React from 'react';
import { Badge } from 'react-bootstrap';
import { STATUS_COLORS, STATUS_ICONS } from '../../utils/constants';

export default function StatusBadge({ status }) {
  const normalizedStatus = status ? status.toUpperCase() : 'UNKNOWN';
  const variant = STATUS_COLORS[normalizedStatus] || 'secondary';
  const icon = STATUS_ICONS[normalizedStatus] || '❓';

  return (
    <Badge bg={variant} className="px-2 py-1">
      <span className="me-1" aria-hidden="true">{icon}</span>
      {normalizedStatus}
    </Badge>
  );
}
