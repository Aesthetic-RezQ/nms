import React from 'react';
import { Badge } from '../bic';
import { STATUS_COLORS } from '../../utils/constants';

export default function StatusBadge({ status, criticality }) {
  const normalizedStatus = status ? status.toUpperCase() : 'UNKNOWN';
  return <span className="bic-status">
    <Badge bg={STATUS_COLORS[normalizedStatus] || 'info'}>{normalizedStatus}</Badge>
    {criticality === 'NON_CRITICAL' && <Badge bg="info">Non-Critical</Badge>}
  </span>;
}
