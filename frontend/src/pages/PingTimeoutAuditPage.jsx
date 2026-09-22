import React, { useEffect, useMemo, useState } from 'react';
import { Card, Table, Form, Row, Col, Button, Badge, Pagination, Spinner } from '../components/bic';
import { MdHistory, MdRefresh, MdSearch } from 'react-icons/md';
import { get } from '../api/client';
import dayjs from 'dayjs';

export default function PingTimeoutAuditPage() {
  const [logs, setLogs] = useState([]);
  const [categories, setCategories] = useState([]);
  const [devices, setDevices] = useState([]);
  const [filters, setFilters] = useState({ category_id: '', device_id: '', reason_code: '', start_time: '', end_time: '' });
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [optionsLoading, setOptionsLoading] = useState(true);
  const [hasSearched, setHasSearched] = useState(false);

  const filteredDevices = useMemo(() => {
    if (!filters.category_id) return devices;
    return devices.filter(device => String(device.category_id || '') === String(filters.category_id));
  }, [devices, filters.category_id]);

  const selectedDevice = devices.find(device => String(device.id) === String(filters.device_id));
  const hasActiveFilters = Object.values(filters).some(Boolean);

  const fetchOptions = async () => {
    try {
      setOptionsLoading(true);
      const [categoryResponse, deviceResponse] = await Promise.all([
        get('/categories'),
        get('/devices?page=1&page_size=500'),
      ]);
      setCategories(categoryResponse.data || []);
      setDevices(deviceResponse.data?.data || []);
    } catch (error) {
      console.error('Failed to load device filters', error);
    } finally {
      setOptionsLoading(false);
    }
  };

  const fetchLogs = async (requestedPage = page) => {
    try {
      setLoading(true);
      const params = new URLSearchParams({ page: String(requestedPage), page_size: '25' });
      if (filters.category_id) params.append('category_id', filters.category_id);
      if (filters.device_id) params.append('device_id', filters.device_id);
      if (filters.reason_code) params.append('reason_code', filters.reason_code);
      if (filters.start_time) params.append('start_time', new Date(filters.start_time).toISOString());
      if (filters.end_time) params.append('end_time', new Date(filters.end_time).toISOString());
      const response = await get(`/ping-timeouts?${params.toString()}`);
      setLogs(response.data.data || []);
      setTotal(response.data.total || 0);
      setTotalPages(response.data.total_pages || 1);
    } catch (error) {
      console.error('Failed to load ping timeout audit', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchOptions(); }, []);

  const updateFilter = (key, value) => {
    setPage(1);
    setHasSearched(false);
    setLogs([]);
    setTotal(0);
    setTotalPages(1);
    setFilters(current => {
      const next = { ...current, [key]: value };
      if (key === 'category_id' && value && !devices.some(device => String(device.id) === String(current.device_id) && String(device.category_id || '') === String(value))) {
        next.device_id = '';
      }
      return next;
    });
  };

  const handleSearch = () => {
    if (!hasActiveFilters) return;
    setPage(1);
    setHasSearched(true);
    fetchLogs(1);
  };

  const handlePageChange = (requestedPage) => {
    setPage(requestedPage);
    fetchLogs(requestedPage);
  };

  return (
    <div>
      <div className="bic-page-header">
        <div>
          <h1 className="bic-page-title bic-flex bic-items-center bic-gap-2"><MdHistory /> Ping Timeout Audit</h1>
          <p className="bic-page-subtitle">Individual ICMP timeout evidence for troubleshooting and incident correlation.</p>
        </div>
        <Button variant="secondary" size="sm" onClick={() => fetchLogs(page)} disabled={!hasSearched || loading}><MdRefresh /> Refresh</Button>
      </div>

      <Card className="bic-mb-6">
        <Card.Body>
          <Row className="bic-items-end">
            <Col md={2} sm={6}>
              <Form.Group><Form.Label>Category</Form.Label><Form.Select aria-label="Filter by category" value={filters.category_id} onChange={event => updateFilter('category_id', event.target.value)} disabled={optionsLoading}>
                <option value="">All Categories</option>{categories.map(category => <option key={category.id} value={category.id}>{category.name}</option>)}
              </Form.Select></Form.Group>
            </Col>
            <Col md={2} sm={6}>
              <Form.Group><Form.Label>Device Name</Form.Label><Form.Select aria-label="Filter by device" value={filters.device_id} onChange={event => updateFilter('device_id', event.target.value)} disabled={optionsLoading}>
                <option value="">All Registered Devices</option>{filteredDevices.map(device => <option key={device.id} value={device.id}>{device.device_name}</option>)}
              </Form.Select></Form.Group>
            </Col>
            <Col md={2} sm={6}>
              <Form.Group><Form.Label>IP Address</Form.Label><Form.Control aria-label="Selected device IP address" value={selectedDevice?.ip_address || '—'} readOnly /></Form.Group>
            </Col>
            <Col md={2} sm={6}>
              <Form.Group><Form.Label>Timeout Reason</Form.Label><Form.Select aria-label="Filter by timeout reason" value={filters.reason_code} onChange={event => updateFilter('reason_code', event.target.value)}>
                <option value="">All Reasons</option><option value="TIMEOUT">TIMEOUT</option><option value="UNREACHABLE">UNREACHABLE</option><option value="ICMP_ERROR">ICMP_ERROR</option>
              </Form.Select></Form.Group>
            </Col>
            <Col md={2} sm={6}>
              <Form.Group><Form.Label>Start Date</Form.Label><Form.Control aria-label="Timeout start date" type="datetime-local" value={filters.start_time} onChange={event => updateFilter('start_time', event.target.value)} /></Form.Group>
            </Col>
            <Col md={2} sm={6}>
              <Form.Group><Form.Label>End Date</Form.Label><div className="bic-input-group"><Form.Control aria-label="Timeout end date" type="datetime-local" value={filters.end_time} onChange={event => updateFilter('end_time', event.target.value)} /><Button variant="primary" size="sm" aria-label="Search timeout audit" title="Search" onClick={handleSearch} disabled={!hasActiveFilters || loading}><MdSearch /></Button></div></Form.Group>
            </Col>
          </Row>
          {!hasActiveFilters && <div className="bic-mt-2 bic-text-secondary bic-text-sm">Apply at least one filter before searching timeout records.</div>}
          {hasSearched && <div className="bic-mt-2 bic-text-right-md bic-text-secondary bic-text-sm">Showing {logs.length} of {total} timeout records</div>}
        </Card.Body>
      </Card>

      <Card>
        <Card.Body className="bic-p-0">
          <Table responsive hover className="bic-mb-0" aria-label="Ping timeout audit records">
            <thead><tr><th>Timestamp</th><th>Device</th><th>IP Address</th><th>Probe</th><th>Timeout</th><th>Reason</th><th>Incident</th></tr></thead>
            <tbody>
              {loading ? <tr><td colSpan="7" className="bic-empty"><Spinner size="sm" /> Loading timeout records...</td></tr> : !hasSearched ? <tr><td colSpan="7" className="bic-empty">Apply a filter, then choose Search to request timeout records.</td></tr> : logs.length ? logs.map(log => (
                <tr key={log.id}><td className="bic-text-sm bic-text-secondary">{dayjs(log.timestamp).format('YYYY-MM-DD HH:mm:ss')}</td><td className="bic-font-semibold">{log.device_name || log.device_id}</td><td><code>{log.ip_address || '—'}</code></td><td>{log.probe_no}</td><td>{log.timeout_ms} ms</td><td><Badge bg={log.reason_code === 'TIMEOUT' ? 'warning' : 'danger'}>{log.reason_code}</Badge></td><td className="bic-text-sm">{log.incident_id ? <code>{log.incident_id}</code> : <span className="bic-text-secondary">Uncorrelated</span>}</td></tr>
              )) : <tr><td colSpan="7" className="bic-empty">No timeout records match the selected filters.</td></tr>}
            </tbody>
          </Table>
        </Card.Body>
        {hasSearched && totalPages > 1 && <Card.Footer className="bic-flex bic-justify-center bic-py-4"><Pagination className="bic-mb-0"><Pagination.Prev disabled={page === 1} onClick={() => handlePageChange(page - 1)} />{[...Array(totalPages)].map((_, index) => <Pagination.Item key={index + 1} active={page === index + 1} onClick={() => handlePageChange(index + 1)}>{index + 1}</Pagination.Item>)}<Pagination.Next disabled={page === totalPages} onClick={() => handlePageChange(page + 1)} /></Pagination></Card.Footer>}
      </Card>
    </div>
  );
}
