import React, { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { Card, Row, Col, Table, Alert, Badge, Button, Spinner } from 'react-bootstrap';
import { MdSpeed, MdWarning, MdCheckCircle, MdError, MdRefresh, MdArrowForward, MdWifiTethering } from 'react-icons/md';
import { get } from '../api/client';
import StatusBadge from '../components/common/StatusBadge';
import dayjs from 'dayjs';

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);

  const fetchSummary = async () => {
    try {
      const res = await get('/dashboard/summary');
      setSummary(res.data);
    } catch (error) {
      console.error('Error fetching dashboard summary:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();

    // Setup WebSocket connection for live status streaming
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/dashboard/ws`;

    const connectWebSocket = () => {
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
          } catch (e) {
            console.error("WS Parse error", e);
          }
        };

        ws.onclose = () => {
          setWsConnected(false);
          // Try reconnect after 5s
          setTimeout(connectWebSocket, 5000);
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
      <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <div>
          <h2 className="mb-0 d-flex align-items-center gap-2">
            Network Dashboard
            {wsConnected && (
              <Badge bg="success" pill style={{ fontSize: '0.65rem' }}>
                <MdWifiTethering /> Live
              </Badge>
            )}
          </h2>
          <p className="text-muted small mb-0">Real-time availability and infrastructure health overview.</p>
        </div>
        <Button variant="outline-secondary" size="sm" onClick={fetchSummary} disabled={loading}>
          <MdRefresh /> Refresh
        </Button>
      </div>

      {/* Stale Worker Banner (PRD §46) */}
      {workerStatus?.is_stale && (
        <Alert variant="warning" className="d-flex align-items-center gap-2 mb-4">
          <MdWarning size={22} className="text-warning" />
          <div>
            <strong>Warning:</strong> {workerStatus.status_message}. Device availability status may not reflect the latest live network state.
          </div>
        </Alert>
      )}

      {/* Status Summary Cards */}
      <Row className="mb-4 g-3">
        <Col lg={2} md={4} sm={6}>
          <Card className="text-center border-0 shadow-sm py-2">
            <Card.Body>
              <div className="text-muted small text-uppercase">Total Devices</div>
              <h2 className="mb-0 fw-bold">{counts.total}</h2>
            </Card.Body>
          </Card>
        </Col>
        <Col lg={2} md={4} sm={6}>
          <Card className="text-center border-0 shadow-sm py-2 border-start border-success border-4">
            <Card.Body>
              <div className="text-success small text-uppercase fw-semibold">UP</div>
              <h2 className="mb-0 text-success fw-bold">{counts.up}</h2>
            </Card.Body>
          </Card>
        </Col>                <Col lg={2} md={4} sm={6}>
          <Card className="text-center border-0 shadow-sm py-2 border-start border-danger border-4">
            <Card.Body>
              <div className="text-danger small text-uppercase fw-semibold">DOWN (Critical)</div>
              <h2 className="mb-0 text-danger fw-bold">{infraCounts.down}</h2>
            </Card.Body>
          </Card>
        </Col>
        <Col lg={2} md={4} sm={6}>
          <Card className="text-center border-0 shadow-sm py-2 border-start border-warning border-4">
            <Card.Body>
              <div className="text-warning small text-uppercase fw-semibold">WARNING</div>
              <h2 className="mb-0 text-warning fw-bold">{counts.warning}</h2>
            </Card.Body>
          </Card>
        </Col>
        <Col lg={2} md={4} sm={6}>
          <Card className="text-center border-0 shadow-sm py-2 border-start border-secondary border-4">
            <Card.Body>
              <div className="text-secondary small text-uppercase fw-semibold">UNKNOWN</div>
              <h2 className="mb-0 text-secondary fw-bold">{counts.unknown}</h2>
            </Card.Body>
          </Card>
        </Col>                <Col lg={2} md={4} sm={6}>
          <Card className="text-center border-0 shadow-sm py-2 border-start border-info border-4">
            <Card.Body>
              <div className="text-info small text-uppercase fw-semibold">MAINTENANCE</div>
              <h2 className="mb-0 text-info fw-bold">{counts.maintenance}</h2>
            </Card.Body>
          </Card>
        </Col>
        <Col lg={2} md={4} sm={6}>
          <Card className="text-center border-0 shadow-sm py-2 border-start border-secondary border-4">
            <Card.Body>
              <div className="text-secondary small text-uppercase fw-semibold">WORKSTATIONS</div>
              <h2 className="mb-0 fw-bold"><span className="text-success">{wsCounts.up}</span> / <span className="text-secondary">{wsCounts.total}</span></h2>
              <div className="text-muted small">Offline: {wsCounts.down}</div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Main Content Grid */}
      <Row className="g-4 mb-4">
        {/* Recent Incidents Card */}
        <Col lg={5}>
          <Card className="border-0 shadow-sm h-100">
            <Card.Header className="bg-white py-3 d-flex justify-content-between align-items-center">
              <h5 className="mb-0 d-flex align-items-center gap-2">
                <MdWarning className="text-danger" /> Active & Recent Incidents
              </h5>
              <Link to="/incidents" className="btn btn-outline-secondary btn-sm">
                View All <MdArrowForward />
              </Link>
            </Card.Header>
            <Card.Body className="p-0">
              <Table responsive hover className="mb-0 align-middle">
                <thead className="table-light">
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
                          <Link to={`/devices/${inc.device_id}`} className="text-decoration-none fw-semibold text-dark">
                            {inc.device_name}
                          </Link>
                          <div className="text-muted small"><code>{inc.ip_address}</code></div>
                        </td>
                        <td className="small">{dayjs(inc.down_since).format('HH:mm:ss')}</td>
                        <td className="small fw-semibold">{inc.duration_formatted || 'Ongoing'}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="4" className="text-center py-4 text-muted">
                        <MdCheckCircle className="text-success me-1" size={18} /> No active outages. All network systems operating normally.
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
          <Card className="border-0 shadow-sm h-100">
            <Card.Header className="bg-white py-3 d-flex justify-content-between align-items-center">
              <h5 className="mb-0 d-flex align-items-center gap-2">
                <MdSpeed className="text-primary" /> Network Health Overview
              </h5>
              <span className="badge bg-light text-dark border">24-Hour Metrics</span>
            </Card.Header>
            <Card.Body className="d-flex flex-column justify-content-center">
              <Row className="text-center g-3 my-auto">
                <Col sm={4}>
                  <div className="text-muted small text-uppercase">Overall Availability</div>
                  <h1 className={`display-5 fw-bold ${summary?.overall_availability_24h < 99 ? 'text-warning' : 'text-success'}`}>
                    {summary?.overall_availability_24h !== undefined ? `${summary.overall_availability_24h}%` : '100%'}
                  </h1>
                </Col>
                <Col sm={4}>
                  <div className="text-muted small text-uppercase">Healthy Devices</div>
                  <h1 className="display-5 fw-bold text-primary">
                    {counts.up} <span className="fs-5 text-muted">/ {counts.total}</span>
                  </h1>
                </Col>
                <Col sm={4}>
                  <div className="text-muted small text-uppercase">Critical Incidents</div>
                  <h1 className={`display-5 fw-bold ${infraCounts.down > 0 ? 'text-danger' : 'text-muted'}`}>
                    {infraCounts.down}
                  </h1>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Live Monitored Devices Table */}
      <Card className="border-0 shadow-sm">
        <Card.Header className="bg-white py-3 d-flex justify-content-between align-items-center">
          <h5 className="mb-0">Monitored Device Overview</h5>
          <Link to="/devices" className="btn btn-outline-primary btn-sm">
            Manage All Devices <MdArrowForward />
          </Link>
        </Card.Header>
        <Card.Body className="p-0">
          <Table responsive hover className="mb-0 align-middle">
            <thead className="table-light">
              <tr>
                <th className="ps-4">Status</th>
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
                  <td colSpan="7" className="text-center py-4">
                    <Spinner animation="border" size="sm" variant="primary" /> Loading devices...
                  </td>
                </tr>
              ) : summary?.recent_devices?.length === 0 ? (
                <tr>
                  <td colSpan="7" className="text-center py-4 text-muted">
                    No devices registered. <Link to="/devices/new">Add a device</Link> to start monitoring.
                  </td>
                </tr>
              ) : (
                summary?.recent_devices?.map((dev) => (
                  <tr key={dev.id}>
                    <td className="ps-4">
                      <StatusBadge status={dev.current_status} />
                    </td>
                    <td>
                      <Link to={`/devices/${dev.id}`} className="fw-semibold text-decoration-none text-dark">
                        {dev.device_name}
                      </Link>
                    </td>
                    <td><code>{dev.ip_address}</code></td>
                    <td>{dev.category_name || '—'}</td>
                    <td>{dev.location_name || '—'}</td>
                    <td>
                      {dev.current_latency !== null ? (
                        <span className={`fw-semibold ${dev.current_latency > 100 ? 'text-warning' : 'text-success'}`}>
                          {dev.current_latency} ms
                        </span>
                      ) : (
                        <span className="text-muted">—</span>
                      )}
                    </td>
                    <td className="small text-muted">
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
