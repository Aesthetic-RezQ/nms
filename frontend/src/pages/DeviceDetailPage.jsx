import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, Row, Col, Button, Table, ButtonGroup, Spinner, Alert, Badge, Stat } from '../components/bic';
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
      
      const [devRes, metRes, incRes] = await Promise.all([
        get(`/devices/${id}`),
        get(`/devices/${id}/metrics`),
        get(`/devices/${id}/incidents?page=1&page_size=10`),
      ]);

      // For 1h use raw history; for 24h/7d use aggregated latency-history
      let histData;
      if (timeRange <= 1) {
        const histRes = await get(`/devices/${id}/history?hours=${timeRange}&limit=500`);
        histData = [...histRes.data].reverse().map(item => ({
          timestamp: item.checked_at,
          latency: item.latency,
          status: item.status,
        }));
      } else {
        const latRes = await get(`/devices/${id}/latency-history?hours=${timeRange}`);
        histData = latRes.data.timestamps.map((ts, i) => ({
          timestamp: ts,
          latency: latRes.data.latencies[i],
          status: latRes.data.statuses[i],
        }));
      }

      setDevice(devRes.data);
      setMetrics(metRes.data);
      setHistory(histData);
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
      <div className="bic-text-center bic-py-10">
        <Spinner />
        <p className="bic-mt-2 bic-text-secondary">Loading device analytics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="danger">
        <Alert.Heading>Error</Alert.Heading>
        <p>{error}</p>
        <Link to="/devices" className="bic-btn bic-btn-secondary bic-btn-sm">
          <MdArrowBack /> Back to Devices
        </Link>
      </Alert>
    );
  }

  // Canvas drawing reads the same BIC tokens as the surrounding UI.
  const styles = getComputedStyle(document.documentElement);
  const token = name => styles.getPropertyValue('--bic-' + name).trim();
  // Chart dataset preparation
  const chartLabels = history.map(item => dayjs(item.timestamp).format(timeRange <= 24 ? 'HH:mm' : 'MMM DD HH:mm'));
  const chartData = {
    labels: chartLabels,
    datasets: [
      {
        label: 'Latency (ms)',
        data: history.map(item => item.latency !== null ? item.latency : null),
        borderColor: token('primary'),
        backgroundColor: token('primary-soft'),
        fill: true,
        tension: 0.3,
        pointRadius: history.length > 50 ? 0 : 3,
        pointHoverRadius: 5
      }
    ]
  };

  const chartOptions = {
    color: token('text-secondary'),
    font: { family: token('font-family'), size: parseFloat(token('font-size-xs')) },
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: token('bg-sidebar'),
        titleColor: token('text-inverse'),
        bodyColor: token('text-inverse'),
        callbacks: {
          label: (context) => `Latency: ${context.parsed.y !== null ? context.parsed.y + ' ms' : 'Offline / Timeout'}`
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: { color: token('text-secondary') },
        title: { display: true, text: 'Latency (ms)', color: token('text-secondary') },
        grid: { color: token('border') }
      },
      x: {
        grid: { display: false },
        ticks: { maxTicksLimit: 12, color: token('text-secondary') }
      }
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="bic-page-header">
        <div className="bic-flex bic-items-center bic-gap-3">
          <Link to="/devices" className="bic-btn bic-btn-secondary bic-btn-sm">
            <MdArrowBack /> Back
          </Link>
          <div>
            <h1 className="bic-page-title bic-flex bic-items-center bic-gap-2">
              {device.device_name}
              <StatusBadge status={device.current_status} criticality={device.criticality} />
            </h1>
            <div className="bic-text-secondary bic-text-sm">
              <code>{device.ip_address}</code> {device.hostname && `(${device.hostname})`}
            </div>
          </div>
        </div>
        <div>
          <Link to={`/devices/${id}/edit`} className="bic-btn bic-btn-primary">
            <MdEdit /> Edit Device
          </Link>
        </div>
      </div>

      <div className="bic-grid bic-grid-4 bic-mb-6">
        <Stat label="24h Availability" value={metrics?.availability_24h != null ? metrics.availability_24h + '%' : 'N/A'} tone={metrics?.availability_24h < 99 ? 'warning' : 'success'} />
        <Stat label="Current Latency" value={device.current_latency != null ? device.current_latency + ' ms' : '—'} />
        <Stat label="Average Latency (24h)" value={metrics?.avg_latency_24h != null ? metrics.avg_latency_24h + ' ms' : '—'} />
        <Stat label="Last Seen" value={device.last_seen ? dayjs(device.last_seen).format('HH:mm:ss') : 'Never'} meta={device.last_seen ? dayjs(device.last_seen).format('YYYY-MM-DD') : undefined} />
      </div>

      {/* Latency History Chart */}
      <Card className="bic-mb-6">
        <Card.Header>
          <h2 className="bic-section-title bic-mb-0 bic-flex bic-items-center bic-gap-2">
            <MdSpeed /> Latency History
          </h2>
          <ButtonGroup size="sm">
            <Button
              variant={timeRange === 1 ? 'primary' : 'secondary'}
              aria-pressed={timeRange === 1}
              onClick={() => setTimeRange(1)}
            >
              1 Hour
            </Button>
            <Button
              variant={timeRange === 24 ? 'primary' : 'secondary'}
              aria-pressed={timeRange === 24}
              onClick={() => setTimeRange(24)}
            >
              24 Hours
            </Button>
            <Button
              variant={timeRange === 168 ? 'primary' : 'secondary'}
              aria-pressed={timeRange === 168}
              onClick={() => setTimeRange(168)}
            >
              7 Days
            </Button>
          </ButtonGroup>
        </Card.Header>
        <Card.Body>
          <div className="bic-chart">
            {history.length > 0 ? (
              <Line data={chartData} options={chartOptions} role="img" aria-label="Device latency over the selected time range, in milliseconds" />
            ) : (
              <div className="bic-flex bic-justify-center bic-items-center bic-h-full bic-text-secondary">
                No latency history recorded yet for this time window.
              </div>
            )}
          </div>
        </Card.Body>
      </Card>

      <Row className="bic-gap-6">
        {/* Device Information */}
        <Col lg={6}>
          <Card className="bic-h-full">
            <Card.Header>
              <h2 className="bic-section-title bic-mb-0 bic-flex bic-items-center bic-gap-2">
                <MdInfo /> Device Details
              </h2>
            </Card.Header>
            <Card.Body className="bic-p-0">
              <Table responsive hover className="bic-mb-0">
                <tbody>
                  <tr>
                    <td className="bic-text-secondary bic-font-semibold bic-detail-label">IP Address</td>
                    <td><code>{device.ip_address}</code></td>
                  </tr>
                  <tr>
                    <td className="bic-text-secondary bic-font-semibold">Criticality</td>
                    <td>
                      <span className="bic-badge bic-badge-info">
                        {device.criticality || 'CRITICAL'}
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td className="bic-text-secondary bic-font-semibold">Hostname</td>
                    <td>{device.hostname || '—'}</td>
                  </tr>
                  <tr>
                    <td className="bic-text-secondary bic-font-semibold">Category</td>
                    <td>{device.category_name || 'Unassigned'}</td>
                  </tr>
                  <tr>
                    <td className="bic-text-secondary bic-font-semibold">Group</td>
                    <td>{device.group_name || 'Unassigned'}</td>
                  </tr>
                  <tr>
                    <td className="bic-text-secondary bic-font-semibold">Location</td>
                    <td>{device.location_name || 'Unassigned'}</td>
                  </tr>
                  <tr>
                    <td className="bic-text-secondary bic-font-semibold">VLAN</td>
                    <td>{device.vlan_id ? `VLAN ${device.vlan_id} (${device.vlan_name || ''})` : '—'}</td>
                  </tr>
                  <tr>
                    <td className="bic-text-secondary bic-font-semibold">Subnet</td>
                    <td>{device.subnet || '—'}</td>
                  </tr>
                  <tr>
                    <td className="bic-text-secondary bic-font-semibold">Monitoring Interval</td>
                    <td>{device.monitoring_interval ? `${device.monitoring_interval}s` : 'Global Default (15s)'}</td>
                  </tr>
                  <tr>
                    <td className="bic-text-secondary bic-font-semibold">Thresholds</td>
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
          <Card className="bic-h-full">
            <Card.Header>
              <h2 className="bic-section-title bic-mb-0 bic-flex bic-items-center bic-gap-2">
                <MdWarning /> Recent Incidents
              </h2>
              <Link to="/incidents" className="bic-btn bic-btn-secondary bic-btn-sm">
                View All
              </Link>
            </Card.Header>
            <Card.Body className="bic-p-0">
              <Table responsive hover className="bic-mb-0">
                <thead>
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
                        <td className="bic-text-sm">{dayjs(inc.detected_at).format('YYYY-MM-DD HH:mm')}</td>
                        <td className="bic-text-sm bic-font-semibold">{inc.duration_formatted || (inc.status === 'RESOLVED' ? '0s' : 'Ongoing')}</td>
                        <td className="bic-text-sm bic-table-note">
                          {inc.failure_reason || '—'}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="4" className="bic-empty">
                        <MdCheckCircle className="bic-text-success bic-mr-1" /> No outages recorded for this device.
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
