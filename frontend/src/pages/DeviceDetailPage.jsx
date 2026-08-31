import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, Row, Col, Button, Table, ButtonGroup, Spinner, Alert, Badge } from 'react-bootstrap';
import { MdArrowBack, MdEdit, MdWarning, MdCheckCircle, MdSpeed, MdAccessTime, MdInfo } from 'react-icons/md';
import { get } from '../api/client';
import StatusBadge from '../components/common/StatusBadge';
import dayjs from 'dayjs';

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function DeviceDetailPage() {
  const { id } = useParams();
  const [device, setDevice] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [history, setHistory] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [timeRange, setTimeRange] = useState(24); // hours: 1, 24, 168 (7 days)
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDeviceData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [devRes, metRes, histRes, incRes] = await Promise.all([
        get(`/devices/${id}`),
        get(`/devices/${id}/metrics`),
        get(`/devices/${id}/history?hours=${timeRange}&limit=300`),
        get(`/devices/${id}/incidents?page=1&page_size=10`)
      ]);

      setDevice(devRes.data);
      setMetrics(metRes.data);
      // History is returned newest-first; reverse for chronological left-to-right chart
      setHistory([...histRes.data].reverse());
      setIncidents(incRes.data.data || []);
    } catch (err) {
      console.error("Failed to load device details", err);
      setError(err.response?.data?.detail || "Failed to load device details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDeviceData();
    const interval = setInterval(fetchDeviceData, 15000);
    return () => clearInterval(interval);
  }, [id, timeRange]);

  if (loading && !device) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" variant="primary" />
        <p className="mt-2 text-muted">Loading device analytics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="danger">
        <Alert.Heading>Error</Alert.Heading>
        <p>{error}</p>
        <Link to="/devices" className="btn btn-outline-danger btn-sm">
          <MdArrowBack /> Back to Devices
        </Link>
      </Alert>
    );
  }

  // Chart dataset preparation
  const chartLabels = history.map(item => dayjs(item.checked_at).format(timeRange <= 24 ? 'HH:mm:ss' : 'MMM DD HH:mm'));
  const chartData = {
    labels: chartLabels,
    datasets: [
      {
        label: 'Latency (ms)',
        data: history.map(item => item.latency !== null ? item.latency : null),
        borderColor: '#0d6efd',
        backgroundColor: 'rgba(13, 110, 253, 0.1)',
        fill: true,
        tension: 0.3,
        pointRadius: history.length > 50 ? 0 : 3,
        pointHoverRadius: 5
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (context) => `Latency: ${context.parsed.y !== null ? context.parsed.y + ' ms' : 'Offline / Timeout'}`
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: { display: true, text: 'Latency (ms)' },
        grid: { color: 'rgba(0,0,0,0.05)' }
      },
      x: {
        grid: { display: false },
        ticks: { maxTicksLimit: 12 }
      }
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <div className="d-flex align-items-center gap-3">
          <Link to="/devices" className="btn btn-outline-secondary btn-sm">
            <MdArrowBack /> Back
          </Link>
          <div>
            <h2 className="mb-0 d-flex align-items-center gap-2">
              {device.device_name}
              <StatusBadge status={device.current_status} criticality={device.criticality} />
            </h2>
            <div className="text-muted small">
              <code>{device.ip_address}</code> {device.hostname && `(${device.hostname})`}
            </div>
          </div>
        </div>
        <div>
          <Link to={`/devices/${id}/edit`} className="btn btn-primary">
            <MdEdit /> Edit Device
          </Link>
        </div>
      </div>

      {/* Metrics Cards */}
      <Row className="g-3 mb-4">
        <Col md={3} sm={6}>
          <Card className="border-0 shadow-sm text-center py-3">
            <div className="text-muted small text-uppercase">24h Availability</div>
            <h3 className={`mt-1 mb-0 ${metrics?.availability_24h < 99 ? 'text-warning' : 'text-success'}`}>
              {metrics?.availability_24h !== undefined ? `${metrics.availability_24h}%` : 'N/A'}
            </h3>
          </Card>
        </Col>
        <Col md={3} sm={6}>
          <Card className="border-0 shadow-sm text-center py-3">
            <div className="text-muted small text-uppercase">Current Latency</div>
            <h3 className="mt-1 mb-0 text-primary">
              {device.current_latency !== null ? `${device.current_latency} ms` : '—'}
            </h3>
          </Card>
        </Col>
        <Col md={3} sm={6}>
          <Card className="border-0 shadow-sm text-center py-3">
            <div className="text-muted small text-uppercase">Average Latency (24h)</div>
            <h3 className="mt-1 mb-0 text-dark">
              {metrics?.avg_latency_24h !== null ? `${metrics?.avg_latency_24h} ms` : '—'}
            </h3>
          </Card>
        </Col>
        <Col md={3} sm={6}>
          <Card className="border-0 shadow-sm text-center py-3">
            <div className="text-muted small text-uppercase">Last Seen</div>
            <h5 className="mt-1 mb-0 text-dark" style={{ fontSize: '1rem' }}>
              {device.last_seen ? dayjs(device.last_seen).format('YYYY-MM-DD HH:mm:ss') : 'Never'}
            </h5>
          </Card>
        </Col>
      </Row>

      {/* Latency History Chart */}
      <Card className="border-0 shadow-sm mb-4">
        <Card.Header className="bg-white py-3 d-flex justify-content-between align-items-center flex-wrap gap-2">
          <h5 className="mb-0 d-flex align-items-center gap-2">
            <MdSpeed /> Latency History
          </h5>
          <ButtonGroup size="sm">
            <Button
              variant={timeRange === 1 ? 'primary' : 'outline-primary'}
              onClick={() => setTimeRange(1)}
            >
              1 Hour
            </Button>
            <Button
              variant={timeRange === 24 ? 'primary' : 'outline-primary'}
              onClick={() => setTimeRange(24)}
            >
              24 Hours
            </Button>
            <Button
              variant={timeRange === 168 ? 'primary' : 'outline-primary'}
              onClick={() => setTimeRange(168)}
            >
              7 Days
            </Button>
          </ButtonGroup>
        </Card.Header>
        <Card.Body>
          <div style={{ height: '280px' }}>
            {history.length > 0 ? (
              <Line data={chartData} options={chartOptions} />
            ) : (
              <div className="d-flex justify-content-center align-items-center h-100 text-muted">
                No latency history recorded yet for this time window.
              </div>
            )}
          </div>
        </Card.Body>
      </Card>

      <Row className="g-4">
        {/* Device Information */}
        <Col lg={6}>
          <Card className="border-0 shadow-sm h-100">
            <Card.Header className="bg-white py-3">
              <h5 className="mb-0 d-flex align-items-center gap-2">
                <MdInfo /> Device Details
              </h5>
            </Card.Header>
            <Card.Body className="p-0">
              <Table responsive hover className="mb-0">
                <tbody>
                  <tr>
                    <td className="text-muted fw-semibold" style={{ width: '35%' }}>IP Address</td>
                    <td><code>{device.ip_address}</code></td>
                  </tr>
                  <tr>
                    <td className="text-muted fw-semibold">Criticality</td>
                    <td>
                      <span className={`badge ${device.criticality === 'NON_CRITICAL' ? 'bg-secondary' : 'bg-danger'}`}>
                        {device.criticality || 'CRITICAL'}
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td className="text-muted fw-semibold">Hostname</td>
                    <td>{device.hostname || '—'}</td>
                  </tr>
                  <tr>
                    <td className="text-muted fw-semibold">Category</td>
                    <td>{device.category_name || 'Unassigned'}</td>
                  </tr>
                  <tr>
                    <td className="text-muted fw-semibold">Group</td>
                    <td>{device.group_name || 'Unassigned'}</td>
                  </tr>
                  <tr>
                    <td className="text-muted fw-semibold">Location</td>
                    <td>{device.location_name || 'Unassigned'}</td>
                  </tr>
                  <tr>
                    <td className="text-muted fw-semibold">VLAN</td>
                    <td>{device.vlan_id ? `VLAN ${device.vlan_id} (${device.vlan_name || ''})` : '—'}</td>
                  </tr>
                  <tr>
                    <td className="text-muted fw-semibold">Subnet</td>
                    <td>{device.subnet || '—'}</td>
                  </tr>
                  <tr>
                    <td className="text-muted fw-semibold">Monitoring Interval</td>
                    <td>{device.monitoring_interval ? `${device.monitoring_interval}s` : 'Global Default (15s)'}</td>
                  </tr>
                  <tr>
                    <td className="text-muted fw-semibold">Thresholds</td>
                    <td>
                      Fail: {device.failure_threshold || 'Default (3)'} | Recovery: {device.recovery_threshold || 'Default (2)'}
                    </td>
                  </tr>
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>

        {/* Device Incident History */}
        <Col lg={6}>
          <Card className="border-0 shadow-sm h-100">
            <Card.Header className="bg-white py-3 d-flex justify-content-between align-items-center">
              <h5 className="mb-0 d-flex align-items-center gap-2">
                <MdWarning /> Recent Incidents
              </h5>
              <Link to="/incidents" className="btn btn-outline-secondary btn-sm">
                View All
              </Link>
            </Card.Header>
            <Card.Body className="p-0">
              <Table responsive hover className="mb-0">
                <thead className="table-light">
                  <tr>
                    <th>Status</th>
                    <th>Detected</th>
                    <th>Downtime</th>
                    <th>Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {incidents.length > 0 ? (
                    incidents.map(inc => (
                      <tr key={inc.id}>
                        <td>
                          <Badge bg={inc.status === 'RESOLVED' ? 'success' : (inc.status === 'ACKNOWLEDGED' ? 'warning' : 'danger')}>
                            {inc.status}
                          </Badge>
                        </td>
                        <td className="small">{dayjs(inc.detected_at).format('YYYY-MM-DD HH:mm')}</td>
                        <td className="small fw-semibold">{inc.duration_formatted || (inc.status === 'RESOLVED' ? '0s' : 'Ongoing')}</td>
                        <td className="small text-truncate" style={{ maxWidth: '140px' }}>
                          {inc.failure_reason || '—'}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="4" className="text-center text-muted py-4">
                        <MdCheckCircle className="text-success me-1" size={18} /> No outages recorded for this device.
                      </td>
                    </tr>
                  )}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
