import React, { useState, useEffect } from 'react';
import { Card, Table, Form, Row, Col, Badge, Button, Modal, Spinner } from 'react-bootstrap';
import { MdSecurity, MdRefresh, MdVisibility, MdFilterList } from 'react-icons/md';
import { get } from '../api/client';
import dayjs from 'dayjs';

export default function AuditLogsPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('');
  const [selectedLog, setSelectedLog] = useState(null);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const query = new URLSearchParams({ page: '1', page_size: '50' });
      if (actionFilter) query.append('action_filter', actionFilter);

      const res = await get(`/audit-logs?${query.toString()}`);
      setLogs(res.data.data || res.data || []);
    } catch (err) {
      console.error("Failed to load audit logs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [actionFilter]);

  const getActionBadgeColor = (action) => {
    if (action.includes('DELETED')) return 'danger';
    if (action.includes('CREATED') || action.includes('ADDED')) return 'success';
    if (action.includes('UPDATED') || action.includes('CHANGED') || action.includes('ACKNOWLEDGED')) return 'warning';
    return 'primary';
  };

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <div>
          <h2 className="mb-0 d-flex align-items-center gap-2">
            <MdSecurity /> Security Audit Logs
          </h2>
          <p className="text-muted small mb-0">Immutable records of administrative operations and configuration changes (PRD §42).</p>
        </div>
        <Button variant="outline-secondary" size="sm" onClick={fetchLogs} disabled={loading}>
          <MdRefresh /> Refresh
        </Button>
      </div>

      {/* Filter Card */}
      <Card className="border-0 shadow-sm mb-4">
        <Card.Body>
          <Row className="g-3 align-items-center">
            <Col md={4} sm={6}>
              <Form.Select
                value={actionFilter}
                onChange={(e) => setActionFilter(e.target.value)}
              >
                <option value="">All Administrative Actions</option>
                <option value="DEVICE_CREATED">Device Created</option>
                <option value="DEVICE_UPDATED">Device Updated</option>
                <option value="DEVICE_DELETED">Device Deleted</option>
                <option value="MAINTENANCE_CREATED">Maintenance Created</option>
                <option value="INCIDENT_ACKNOWLEDGED">Incident Acknowledged</option>
                <option value="SETTING_CHANGED">Settings Changed</option>
                <option value="USER_LOGIN">User Login</option>
              </Form.Select>
            </Col>
            <Col md={8} className="text-md-end text-muted small">
              Showing recent 50 audit entries
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* Audit Log Table */}
      <Card className="border-0 shadow-sm">
        <Card.Body className="p-0">
          <Table responsive hover className="mb-0 align-middle">
            <thead className="table-light">
              <tr>
                <th>Timestamp</th>
                <th>Operator</th>
                <th>Action</th>
                <th>Target Object</th>
                <th>Source IP</th>
                <th className="text-end pe-3">Changes</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="6" className="text-center py-5 text-muted">
                    <Spinner animation="border" size="sm" variant="primary" /> Loading audit logs...
                  </td>
                </tr>
              ) : logs.length > 0 ? (
                logs.map((log) => (
                  <tr key={log.id}>
                    <td className="small text-muted">{dayjs(log.created_at).format('YYYY-MM-DD HH:mm:ss')}</td>
                    <td className="fw-semibold small">{log.username || 'System'}</td>
                    <td>
                      <Badge bg={getActionBadgeColor(log.action)}>
                        {log.action}
                      </Badge>
                    </td>
                    <td className="small">
                      <code>{log.object_type || '—'}</code> {log.object_id && `(${log.object_id})`}
                    </td>
                    <td className="small text-muted">{log.source_ip || '—'}</td>
                    <td className="text-end pe-3">
                      {(log.old_value || log.new_value) && (
                        <Button
                          variant="outline-secondary"
                          size="sm"
                          onClick={() => setSelectedLog(log)}
                          title="View change payload"
                        >
                          <MdVisibility /> Diff
                        </Button>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="6" className="text-center py-5 text-muted">
                    No audit records found matching criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </Table>
        </Card.Body>
      </Card>

      {/* Diff / Payload Modal */}
      <Modal show={!!selectedLog} onHide={() => setSelectedLog(null)} size="lg" centered>
        <Modal.Header closeButton>
          <Modal.Title className="h5">
            Audit Details: {selectedLog?.action}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Row className="g-3">
            {selectedLog?.old_value && (
              <Col md={6}>
                <h6 className="text-muted small text-uppercase">Previous State</h6>
                <pre className="bg-light p-3 rounded small" style={{ maxHeight: '250px', overflowY: 'auto' }}>
                  {JSON.stringify(selectedLog.old_value, null, 2)}
                </pre>
              </Col>
            )}
            {selectedLog?.new_value && (
              <Col md={selectedLog?.old_value ? 6 : 12}>
                <h6 className="text-muted small text-uppercase">New State / Payload</h6>
                <pre className="bg-light p-3 rounded small" style={{ maxHeight: '250px', overflowY: 'auto' }}>
                  {JSON.stringify(selectedLog.new_value, null, 2)}
                </pre>
              </Col>
            )}
          </Row>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setSelectedLog(null)}>Close</Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}
