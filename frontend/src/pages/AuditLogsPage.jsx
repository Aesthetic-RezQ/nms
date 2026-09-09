import React, { useState, useEffect } from 'react';
import { Card, Table, Form, Row, Col, Badge, Button, Modal, Spinner } from '../components/bic';
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
    return 'info';
  };

  return (
    <div>
      <div className="bic-page-header">
        <div>
          <h1 className="bic-page-title bic-flex bic-items-center bic-gap-2">
            <MdSecurity /> Security Audit Logs
          </h1>
          <p className="bic-page-subtitle">Immutable records of administrative operations and configuration changes.</p>
        </div>
        <Button variant="secondary" size="sm" onClick={fetchLogs} disabled={loading}>
          <MdRefresh /> Refresh
        </Button>
      </div>

      {/* Filter Card */}
      <Card className="bic-mb-6">
        <Card.Body>
          <Row className="bic-items-center">
            <Col md={4} sm={6}>
              <Form.Select
                aria-label="Filter by administrative action"
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
            <Col md={8} className="bic-text-right-md bic-text-secondary bic-text-sm">
              Showing recent 50 audit entries
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* Audit Log Table */}
      <Card>
        <Card.Body className="bic-p-0">
          <Table responsive hover className="bic-mb-0">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Operator</th>
                <th>Action</th>
                <th>Target Object</th>
                <th>Source IP</th>
                <th className="bic-text-right bic-pr-4">Changes</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="6" className="bic-empty">
                    <Spinner size="sm" /> Loading audit logs...
                  </td>
                </tr>
              ) : logs.length > 0 ? (
                logs.map((log) => (
                  <tr key={log.id}>
                    <td className="bic-text-sm bic-text-secondary">{dayjs(log.created_at).format('YYYY-MM-DD HH:mm:ss')}</td>
                    <td className="bic-font-semibold bic-text-sm">{log.username || 'System'}</td>
                    <td>
                      <Badge bg={getActionBadgeColor(log.action)}>
                        {log.action}
                      </Badge>
                    </td>
                    <td className="bic-text-sm">
                      <code>{log.object_type || '—'}</code> {log.object_id && `(${log.object_id})`}
                    </td>
                    <td className="bic-text-sm bic-text-secondary">{log.source_ip || '—'}</td>
                    <td className="bic-text-right bic-pr-4">
                      {(log.old_value || log.new_value) && (
                        <Button
                          variant="secondary"
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
                  <td colSpan="6" className="bic-empty">
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
          <Modal.Title>
            Audit Details: {selectedLog?.action}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Row>
            {selectedLog?.old_value && (
              <Col md={6}>
                <h3 className="bic-text-secondary bic-text-sm">Previous State</h3>
                <pre className="bic-code-block">
                  {JSON.stringify(selectedLog.old_value, null, 2)}
                </pre>
              </Col>
            )}
            {selectedLog?.new_value && (
              <Col md={selectedLog?.old_value ? 6 : 12}>
                <h3 className="bic-text-secondary bic-text-sm">New State / Payload</h3>
                <pre className="bic-code-block">
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
