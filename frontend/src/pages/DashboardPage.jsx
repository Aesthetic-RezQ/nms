import React, { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { Card, Row, Col, Table, Alert, Badge, Button, Spinner, Stat } from '../components/bic';
import { MdSpeed, MdWarning, MdCheckCircle, MdError, MdRefresh, MdArrowForward, MdWifiTethering } from 'react-icons/md';
import { get } from '../api/client';
import StatusBadge from '../components/common/StatusBadge';
import dayjs from 'dayjs';

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);

  const fetchSummary = async () => {
    setLoading(true);
    try {
      const res = await get('/dashboard/summary');
      setSummary(res.data);
      setError('');
    } catch (error) {
      console.error('Error fetching dashboard summary:', error);
      setError('Unable to refresh network health. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
    let stopped = false;
    let reconnectTimeout;

    // Setup WebSocket connection for live status streaming
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/dashboard/ws`;

    const connectWebSocket = () => {
      if (stopped) return;
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setWsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            setSummary(data);
            setError('');
          } catch (e) {
            console.error("WS Parse error", e);
          }
        };

        ws.onclose = () => {
          setWsConnected(false);
          // Try reconnect after 5s
          if (!stopped) reconnectTimeout = setTimeout(connectWebSocket, 5000);
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch (err) {
        console.warn("WebSocket not supported or connection failed, falling back to HTTP polling", err);
      }
    };

    connectWebSocket();

    // Fallback polling interval every 15s in case WS is interrupted
    const interval = setInterval(fetchSummary, 15000);

    return () => {
      stopped = true;
      clearTimeout(reconnectTimeout);
      clearInterval(interval);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const counts = summary?.status_counts || { total: 0, up: 0, down: 0, warning: 0, unknown: 0, maintenance: 0 };
  const infraCounts = summary?.infrastructure_counts || { total: 0, up: 0, down: 0, warning: 0 };
  const wsCounts = summary?.workstation_counts || { total: 0, up: 0, down: 0 };
  const workerStatus = summary?.worker_status;

  return (
    <div>
      {/* Top Header */}
      <div className="bic-page-header">
        <div>
          <h1 className="bic-page-title bic-flex bic-items-center bic-gap-2">
            Network Dashboard
            {wsConnected && (
              <Badge bg="success">
                <MdWifiTethering /> Live
              </Badge>
            )}
          </h1>
          <p className="bic-page-subtitle">Real-time availability and infrastructure health overview.</p>
        </div>
        <Button variant="secondary" size="sm" onClick={fetchSummary} disabled={loading}>
          <MdRefresh /> Refresh
        </Button>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      {/* Stale Worker Banner (PRD §46) */}
      {workerStatus?.is_stale && (
        <Alert variant="warning" className="bic-flex bic-items-center bic-gap-2 bic-mb-6">
          <MdWarning className="bic-text-warning" />
          <div>
            <strong>Warning:</strong> {workerStatus.status_message}. Device availability status may not reflect the latest live network state.
          </div>
        </Alert>
      )}

      <div className="bic-grid bic-grid-4 bic-mb-6">
        <Stat label="Total Devices" value={summary ? counts.total : '—'} />
        <Stat label="UP" value={summary ? counts.up : '—'} tone="success" />
        <Stat label="DOWN (Critical)" value={summary ? infraCounts.down : '—'} tone="danger" />
        <Stat label="Warning" value={summary ? counts.warning : '—'} tone="warning" />
        <Stat label="Unknown" value={summary ? counts.unknown : '—'} tone="info" />
        <Stat label="Maintenance" value={summary ? counts.maintenance : '—'} tone="info" />
        <Stat label="Workstations" value={summary ? wsCounts.up + ' / ' + wsCounts.total : '—'} meta={summary ? 'Offline: ' + wsCounts.down : undefined} />
      </div>

      {/* Main Content Grid */}
      <Row className="bic-gap-6 bic-mb-6">
        {/* Recent Incidents Card */}
        <Col lg={5}>
          <Card className="bic-h-full">
            <Card.Header>
              <h2 className="bic-section-title bic-mb-0 bic-flex bic-items-center bic-gap-2">
                <MdWarning /> Active & Recent Incidents
              </h2>
              <Link to="/incidents" className="bic-btn bic-btn-secondary bic-btn-sm">
                View All <MdArrowForward />
              </Link>
            </Card.Header>
            <Card.Body className="bic-p-0">
              <Table responsive hover className="bic-mb-0">
                <thead>
                  <tr>
                    <th>Status</th>
                    <th>Device</th>
                    <th>Down Since</th>
                    <th>Downtime</th>
                  </tr>
                </thead>
                <tbody>
                  {summary?.recent_incidents?.length > 0 ? (
                    summary.recent_incidents.map((inc) => (
                      <tr key={inc.id}>
                        <td>
                          <Badge bg={inc.status === 'RESOLVED' ? 'success' : (inc.status === 'ACKNOWLEDGED' ? 'warning' : 'danger')}>
                            {inc.status}
                          </Badge>
                        </td>
                        <td>
                          <Link to={`/devices/${inc.device_id}`} className="bic-font-semibold bic-text-primary">
                            {inc.device_name}
                          </Link>
                          <div className="bic-text-secondary bic-text-sm"><code>{inc.ip_address}</code></div>
                        </td>
                        <td className="bic-text-sm">{dayjs(inc.down_since).format('HH:mm:ss')}</td>
                        <td className="bic-text-sm bic-font-semibold">{inc.duration_formatted || 'Ongoing'}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="4" className="bic-empty">
                        {summary && <MdCheckCircle className="bic-text-success bic-mr-1" />} {summary ? 'No recent incidents recorded.' : loading ? 'Loading incidents...' : 'Incident data is unavailable.'}
                      </td>
                    </tr>
                  )}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>

        {/* 24h Network Availability & Quick Stats */}
        <Col lg={7}>
          <Card className="bic-h-full">
            <Card.Header>
              <h2 className="bic-section-title bic-mb-0 bic-flex bic-items-center bic-gap-2">
                <MdSpeed className="bic-text-brand" /> Network Health Overview
              </h2>
              <span className="bic-badge bic-badge-info">24-Hour Metrics</span>
            </Card.Header>
            <Card.Body className="bic-flex bic-flex-column bic-justify-center">
              <Row className="bic-text-center bic-my-auto">
                <Col sm={4}>
                  <div className="bic-stat-label">Overall Availability</div>
                  <div className={`bic-stat-value bic-font-bold ${summary?.overall_availability_24h < 99 ? 'bic-text-warning' : 'bic-text-success'}`}>
                    {summary?.overall_availability_24h !== undefined ? `${summary.overall_availability_24h}%` : '—'}
                  </div>
                </Col>
                <Col sm={4}>
                  <div className="bic-stat-label">Healthy Devices</div>
                  <div className="bic-stat-value bic-font-bold bic-text-brand">
                    {counts.up} <span className="bic-text-lg bic-text-secondary">/ {counts.total}</span>
                  </div>
                </Col>
                <Col sm={4}>
                  <div className="bic-stat-label">Critical Incidents</div>
                  <div className={`bic-stat-value bic-font-bold ${infraCounts.down > 0 ? 'bic-text-danger' : 'bic-text-secondary'}`}>
                    {infraCounts.down}
                  </div>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Live Monitored Devices Table */}
      <Card>
        <Card.Header>
          <h2 className="bic-section-title bic-mb-0">Monitored Device Overview</h2>
          <Link to="/devices" className="bic-btn bic-btn-secondary bic-btn-sm">
            Manage All Devices <MdArrowForward />
          </Link>
        </Card.Header>
        <Card.Body className="bic-p-0">
          <Table responsive hover className="bic-mb-0">
            <thead>
              <tr>
                <th className="bic-pl-6">Status</th>
                <th>Device Name</th>
                <th>IP Address</th>
                <th>Category</th>
                <th>Location</th>
                <th>Latency</th>
                <th>Last Check</th>
              </tr>
            </thead>
            <tbody>
              {loading && !summary ? (
                <tr>
                  <td colSpan="7" className="bic-empty">
                    <Spinner size="sm" /> Loading devices...
                  </td>
                </tr>
              ) : summary?.recent_devices?.length === 0 ? (
                <tr>
                  <td colSpan="7" className="bic-empty">
                    No devices registered. <Link to="/devices/new">Add a device</Link> to start monitoring.
                  </td>
                </tr>
              ) : (
                summary?.recent_devices?.map((dev) => (
                  <tr key={dev.id}>
                    <td className="bic-pl-6">
                      <StatusBadge status={dev.current_status} />
                    </td>
                    <td>
                      <Link to={`/devices/${dev.id}`} className="bic-font-semibold bic-text-primary">
                        {dev.device_name}
                      </Link>
                    </td>
                    <td><code>{dev.ip_address}</code></td>
                    <td>{dev.category_name || '—'}</td>
                    <td>{dev.location_name || '—'}</td>
                    <td>
                      {dev.current_latency !== null ? (
                        <span className={`bic-font-semibold ${dev.current_latency > 100 ? 'bic-text-warning' : 'bic-text-success'}`}>
                          {dev.current_latency} ms
                        </span>
                      ) : (
                        <span className="bic-text-secondary">—</span>
                      )}
                    </td>
                    <td className="bic-text-sm bic-text-secondary">
                      {dev.last_check ? dayjs(dev.last_check).format('HH:mm:ss') : 'Pending'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </Table>
        </Card.Body>
      </Card>
    </div>
  );
}
