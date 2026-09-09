import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, Table, Form, Row, Col, Button, Badge, Modal, Pagination, Spinner, Alert } from '../components/bic';
import { MdWarning, MdCheck, MdNoteAdd, MdRefresh, MdFilterList } from 'react-icons/md';
import { get, post } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { toast } from '../components/bic/Notifications';
import dayjs from 'dayjs';

export default function IncidentsPage() {
  const { isOperator, isAdmin } = useAuth();
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  // Acknowledge modal state
  const [showAckModal, setShowAckModal] = useState(false);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [ackNotes, setAckNotes] = useState('');
  const [ackSubmitting, setAckSubmitting] = useState(false);

  // Note modal state
  const [showNoteModal, setShowNoteModal] = useState(false);
  const [noteContent, setNoteContent] = useState('');
  const [noteSubmitting, setNoteSubmitting] = useState(false);

  const fetchIncidents = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: '20'
      });
      if (statusFilter) params.append('status', statusFilter);
      if (search) params.append('search', search);

      const res = await get(`/incidents?${params.toString()}`);
      setIncidents(res.data.data || []);
      setTotalPages(res.data.total_pages || 1);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error("Failed to load incidents", err);
      toast.error("Failed to load incident records");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
    const interval = setInterval(fetchIncidents, 10000);
    return () => clearInterval(interval);
  }, [page, statusFilter, search]);

  const handleOpenAcknowledge = (incident) => {
    setSelectedIncident(incident);
    setAckNotes('');
    setShowAckModal(true);
  };

  const handleConfirmAcknowledge = async (e) => {
    e.preventDefault();
    if (!selectedIncident) return;
    try {
      setAckSubmitting(true);
      await post(`/incidents/${selectedIncident.id}/acknowledge`, { notes: ackNotes || undefined });
      toast.success(`Incident for ${selectedIncident.device_name} acknowledged`);
      setShowAckModal(false);
      fetchIncidents();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to acknowledge incident");
    } finally {
      setAckSubmitting(false);
    }
  };

  const handleOpenAddNote = (incident) => {
    setSelectedIncident(incident);
    setNoteContent('');
    setShowNoteModal(true);
  };

  const handleConfirmAddNote = async (e) => {
    e.preventDefault();
    if (!selectedIncident || !noteContent.trim()) return;
    try {
      setNoteSubmitting(true);
      await post(`/incidents/${selectedIncident.id}/notes`, { notes: noteContent });
      toast.success("Note added successfully");
      setShowNoteModal(false);
      fetchIncidents();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to add note");
    } finally {
      setNoteSubmitting(false);
    }
  };

  return (
    <div>
      <div className="bic-page-header">
        <div>
          <h1 className="bic-page-title bic-flex bic-items-center bic-gap-2">
            <MdWarning /> Incident Management
          </h1>
          <p className="bic-page-subtitle">Track network outages, downtime, and operational resolution.</p>
        </div>
        <Button variant="secondary" size="sm" onClick={fetchIncidents} disabled={loading}>
          <MdRefresh /> Refresh
        </Button>
      </div>

      {/* Filter Bar */}
      <Card className="bic-mb-6">
        <Card.Body>
          <Row className="bic-items-center">
            <Col md={4} sm={6}>
              <Form.Select
                aria-label="Filter by incident status"
                value={statusFilter}
                onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
              >
                <option value="">All Statuses</option>
                <option value="OPEN">OPEN (Active Outages)</option>
                <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
                <option value="RESOLVED">RESOLVED</option>
              </Form.Select>
            </Col>
            <Col md={5} sm={6}>
              <Form.Control
                type="text"
                aria-label="Search incidents"
                placeholder="Search by device, IP, or reason..."
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              />
            </Col>
            <Col md={3} className="bic-text-right-md bic-text-secondary bic-text-sm">
              Found <strong>{total}</strong> incident{total !== 1 ? 's' : ''}
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* Incidents Table */}
      <Card>
        <Card.Body className="bic-p-0">
          <Table responsive hover className="bic-mb-0">
            <thead>
              <tr>
                <th>Status</th>
                <th>Device</th>
                <th>Down Since</th>
                <th>Recovered / Duration</th>
                <th>Failure Reason</th>
                <th>Acknowledged</th>
                {(isOperator || isAdmin) && <th className="bic-text-right">Actions</th>}
              </tr>
            </thead>
            <tbody>
              {loading && incidents.length === 0 ? (
                <tr>
                  <td colSpan="7" className="bic-empty">
                    <Spinner size="sm" />
                    <span className="bic-ml-2 bic-text-secondary">Loading incidents...</span>
                  </td>
                </tr>
              ) : incidents.length > 0 ? (
                incidents.map((inc) => (
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
                      <div className="bic-text-secondary bic-text-sm">
                        <code>{inc.ip_address}</code> {inc.location_name && `• ${inc.location_name}`}
                      </div>
                    </td>
                    <td className="bic-text-sm">
                      {dayjs(inc.down_since).format('YYYY-MM-DD HH:mm:ss')}
                    </td>
                    <td className="bic-text-sm">
                      {inc.recovered_at ? (
                        <>
                          <div>{dayjs(inc.recovered_at).format('YYYY-MM-DD HH:mm:ss')}</div>
                          <strong className="bic-text-success">{inc.duration_formatted}</strong>
                        </>
                      ) : (
                        <Badge bg="danger">Ongoing Outage</Badge>
                      )}
                    </td>
                    <td className="bic-text-sm bic-text-secondary bic-table-note">
                      {inc.failure_reason || '—'}
                    </td>
                    <td className="bic-text-sm">
                      {inc.is_acknowledged ? (
                        <div>
                          <span className="bic-text-success bic-font-semibold">✓ {inc.acknowledged_by_name || 'Staff'}</span>
                          <div className="bic-text-secondary bic-text-xs">
                            {dayjs(inc.acknowledged_at).format('HH:mm:ss')}
                          </div>
                        </div>
                      ) : (
                        <span className="bic-text-secondary">—</span>
                      )}
                    </td>
                    {(isOperator || isAdmin) && (
                      <td className="bic-text-right">
                        <div className="bic-button-group bic-button-group-sm">
                          {!inc.is_acknowledged && inc.status !== 'RESOLVED' && (
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() => handleOpenAcknowledge(inc)}
                              title="Acknowledge Incident"
                            >
                              <MdCheck /> Ack
                            </Button>
                          )}
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handleOpenAddNote(inc)}
                            title="Add Note"
                          >
                            <MdNoteAdd /> Note
                          </Button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="7" className="bic-empty">
                    No incidents matching your filter criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </Table>
        </Card.Body>

        {/* Pagination */}
        {totalPages > 1 && (
          <Card.Footer className="bic-flex bic-justify-center bic-py-4">
            <Pagination className="bic-mb-0">
              <Pagination.Prev disabled={page === 1} onClick={() => setPage(p => p - 1)} />
              {[...Array(totalPages)].map((_, i) => (
                <Pagination.Item key={i + 1} active={i + 1 === page} onClick={() => setPage(i + 1)}>
                  {i + 1}
                </Pagination.Item>
              ))}
              <Pagination.Next disabled={page === totalPages} onClick={() => setPage(p => p + 1)} />
            </Pagination>
          </Card.Footer>
        )}
      </Card>

      {/* Acknowledge Modal */}
      <Modal show={showAckModal} onHide={() => setShowAckModal(false)} centered>
        <Form onSubmit={handleConfirmAcknowledge}>
          <Modal.Header closeButton>
            <Modal.Title>Acknowledge Incident</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <p>
              Are you acknowledging the outage on <strong>{selectedIncident?.device_name}</strong> (<code>{selectedIncident?.ip_address}</code>)?
            </p>
            <Form.Group className="bic-mb-4">
              <Form.Label>Investigation Notes (Optional)</Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                placeholder="e.g. Checking core switch power supply / technician on site"
                value={ackNotes}
                onChange={(e) => setAckNotes(e.target.value)}
              />
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowAckModal(false)}>Cancel</Button>
            <Button variant="primary" type="submit" disabled={ackSubmitting}>
              {ackSubmitting ? 'Acknowledging...' : 'Confirm Acknowledge'}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>

      {/* Add Note Modal */}
      <Modal show={showNoteModal} onHide={() => setShowNoteModal(false)} centered>
        <Form onSubmit={handleConfirmAddNote}>
          <Modal.Header closeButton>
            <Modal.Title>Add Incident Note</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            {selectedIncident?.notes && (
              <div className="bic-inset bic-p-2 bic-mb-4 bic-text-sm bic-scroll-area-sm">
                <div className="bic-font-semibold bic-text-secondary bic-mb-1">Previous Notes:</div>
                <pre className="bic-mb-0 bic-text-primary bic-pre-wrap">
                  {selectedIncident.notes}
                </pre>
              </div>
            )}
            <Form.Group className="bic-mb-4">
              <Form.Label>New Note</Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                required
                placeholder="Enter investigation updates or root cause findings..."
                value={noteContent}
                onChange={(e) => setNoteContent(e.target.value)}
              />
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowNoteModal(false)}>Cancel</Button>
            <Button variant="primary" type="submit" disabled={noteSubmitting}>
              {noteSubmitting ? 'Saving...' : 'Add Note'}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </div>
  );
}
