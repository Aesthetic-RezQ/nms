import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Modal, Form, Row, Col, Badge, Spinner } from '../components/bic';
import { MdAdd, MdEdit, MdDelete, MdBuild, MdCheckCircle, MdAccessTime } from 'react-icons/md';
import { toast } from '../components/bic/Notifications';
import { get, post, put, del } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import ConfirmDialog from '../components/common/ConfirmDialog';
import dayjs from 'dayjs';

export default function MaintenancePage() {
  const { isAdmin } = useAuth();
  const [windows, setWindows] = useState([]);
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    start_time: '',
    end_time: '',
    is_active: true,
    device_ids: []
  });
  const [submitting, setSubmitting] = useState(false);
  const [deleteId, setDeleteId] = useState(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [winRes, devRes] = await Promise.all([
        get('/maintenance'),
        get('/devices?page_size=300')
      ]);
      setWindows(winRes.data || []);
      setDevices(devRes.data.data || devRes.data.items || devRes.data || []);
    } catch (err) {
      console.error("Error loading maintenance data", err);
      toast.error("Failed to load maintenance windows");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleOpenCreate = () => {
    setEditingId(null);
    const now = dayjs();
    setFormData({
      name: '',
      description: '',
      start_time: now.format('YYYY-MM-DDTHH:mm'),
      end_time: now.add(2, 'hour').format('YYYY-MM-DDTHH:mm'),
      is_active: true,
      device_ids: []
    });
    setShowModal(true);
  };

  const handleOpenEdit = (win) => {
    setEditingId(win.id);
    setFormData({
      name: win.name,
      description: win.description || '',
      start_time: dayjs(win.start_time).format('YYYY-MM-DDTHH:mm'),
      end_time: dayjs(win.end_time).format('YYYY-MM-DDTHH:mm'),
      is_active: win.is_active,
      device_ids: win.device_ids || []
    });
    setShowModal(true);
  };

  const handleDeviceToggle = (deviceId) => {
    setFormData(prev => {
      const ids = new Set(prev.device_ids);
      if (ids.has(deviceId)) {
        ids.delete(deviceId);
      } else {
        ids.add(deviceId);
      }
      return { ...prev, device_ids: Array.from(ids) };
    });
  };

  const handleSelectAllDevices = () => {
    setFormData(prev => ({
      ...prev,
      device_ids: devices.map(d => d.id)
    }));
  };

  const handleDeselectAllDevices = () => {
    setFormData(prev => ({
      ...prev,
      device_ids: []
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (dayjs(formData.start_time).isAfter(dayjs(formData.end_time))) {
      toast.error("End time must be after start time");
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        name: formData.name,
        description: formData.description || null,
        start_time: new Date(formData.start_time).toISOString(),
        end_time: new Date(formData.end_time).toISOString(),
        is_active: formData.is_active,
        device_ids: formData.device_ids
      };

      if (editingId) {
        await put(`/maintenance/${editingId}`, payload);
        toast.success("Maintenance window updated");
      } else {
        await post('/maintenance', payload);
        toast.success("Maintenance window scheduled");
      }
      setShowModal(false);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to save maintenance window");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    try {
      await del(`/maintenance/${deleteId}`);
      toast.success("Maintenance window deleted");
      fetchData();
    } catch (err) {
      toast.error("Failed to delete maintenance window");
    } finally {
      setDeleteId(null);
    }
  };

  return (
    <div>
      <div className="bic-page-header">
        <div>
          <h1 className="bic-page-title bic-flex bic-items-center bic-gap-2">
            <MdBuild /> Maintenance Windows
          </h1>
          <p className="bic-page-subtitle">Schedule planned maintenance periods to suppress outage alarms.</p>
        </div>
        {isAdmin && (
          <Button variant="primary" onClick={handleOpenCreate}>
            <MdAdd className="bic-mr-1" /> Schedule Maintenance
          </Button>
        )}
      </div>

      <Card className="bic-mb-6">
        <Card.Body className="bic-p-0">
          <Table responsive hover className="bic-mb-0">
            <thead>
              <tr>
                <th>Status</th>
                <th>Name / Description</th>
                <th>Start Time</th>
                <th>End Time</th>
                <th>Assigned Devices</th>
                <th>Created By</th>
                {isAdmin && <th className="bic-text-right bic-pr-4">Actions</th>}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7" className="bic-empty">
                    <Spinner size="sm" /> Loading windows...
                  </td>
                </tr>
              ) : windows.length > 0 ? (
                windows.map((win) => (
                  <tr key={win.id}>
                    <td>
                      {win.is_currently_active ? (
                        <Badge bg="info">ACTIVE NOW</Badge>
                      ) : !win.is_active ? (
                        <Badge bg="info">Disabled</Badge>
                      ) : dayjs().isAfter(win.end_time) ? (
                        <Badge bg="info">Ended</Badge>
                      ) : (
                        <Badge bg="info">Scheduled</Badge>
                      )}
                    </td>
                    <td>
                      <div className="bic-font-semibold bic-text-primary">{win.name}</div>
                      {win.description && <div className="bic-text-secondary bic-text-sm">{win.description}</div>}
                    </td>
                    <td className="bic-text-sm">{dayjs(win.start_time).format('YYYY-MM-DD HH:mm')}</td>
                    <td className="bic-text-sm">{dayjs(win.end_time).format('YYYY-MM-DD HH:mm')}</td>
                    <td>
                      <Badge bg="info">
                        {win.devices_count} device{win.devices_count !== 1 ? 's' : ''}
                      </Badge>
                    </td>
                    <td className="bic-text-sm bic-text-secondary">{win.created_by_name || 'Admin'}</td>
                    {isAdmin && (
                      <td className="bic-text-right bic-pr-4">
                        <div className="bic-button-group bic-button-group-sm">
                          <Button variant="secondary" onClick={() => handleOpenEdit(win)} title="Edit">
                            <MdEdit />
                          </Button>
                          <Button variant="danger" onClick={() => setDeleteId(win.id)} title="Delete">
                            <MdDelete />
                          </Button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="7" className="bic-empty">
                    No scheduled maintenance windows.
                  </td>
                </tr>
              )}
            </tbody>
          </Table>
        </Card.Body>
      </Card>

      {/* Schedule / Edit Modal */}
      <Modal show={showModal} onHide={() => setShowModal(false)} size="lg" centered>
        <Form onSubmit={handleSubmit}>
          <Modal.Header closeButton>
            <Modal.Title>
              {editingId ? 'Edit Maintenance Window' : 'Schedule Maintenance Window'}
            </Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Row className="bic-mb-4">
              <Col md={8}>
                <Form.Group>
                  <Form.Label>Window Name *</Form.Label>
                  <Form.Control
                    type="text"
                    required
                    placeholder="e.g. Core Switch Firmware Upgrade"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                </Form.Group>
              </Col>
              <Col md={4} className="bic-flex bic-items-end">
                <Form.Check
                  type="checkbox"
                  id="active-chk"
                  label="Maintenance Enabled"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                />
              </Col>
            </Row>

            <Form.Group className="bic-mb-4">
              <Form.Label>Description (Optional)</Form.Label>
              <Form.Control
                as="textarea"
                rows={2}
                placeholder="Details about planned maintenance activities..."
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </Form.Group>

            <Row className="bic-mb-4">
              <Col md={6}>
                <Form.Group>
                  <Form.Label>Start Time *</Form.Label>
                  <Form.Control
                    type="datetime-local"
                    required
                    value={formData.start_time}
                    onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                  />
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group>
                  <Form.Label>End Time *</Form.Label>
                  <Form.Control
                    type="datetime-local"
                    required
                    value={formData.end_time}
                    onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                  />
                </Form.Group>
              </Col>
            </Row>

            <Form.Group className="bic-mb-4">
              <div className="bic-flex bic-justify-between bic-items-center bic-mb-2">
                <span id="affected-devices-label" className="bic-label bic-mb-0">
                  Affected Devices ({formData.device_ids.length} selected)
                </span>
                <div className="bic-button-group bic-button-group-sm">
                  <Button variant="secondary" size="sm" onClick={handleSelectAllDevices}>Select All</Button>
                  <Button variant="secondary" size="sm" onClick={handleDeselectAllDevices}>Deselect All</Button>
                </div>
              </div>
              <div className="bic-inset bic-scroll-area" role="group" aria-labelledby="affected-devices-label">
                <Row className="bic-gap-2">
                  {devices.map(dev => (
                    <Col md={6} key={dev.id}>
                      <Form.Check
                        type="checkbox"
                        id={`dev-${dev.id}`}
                        label={`${dev.device_name} (${dev.ip_address})`}
                        checked={formData.device_ids.includes(dev.id)}
                        onChange={() => handleDeviceToggle(dev.id)}
                      />
                    </Col>
                  ))}
                </Row>
              </div>
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowModal(false)}>Cancel</Button>
            <Button variant="primary" type="submit" disabled={submitting}>
              {submitting ? 'Saving...' : 'Save Maintenance Window'}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>

      <ConfirmDialog
        show={!!deleteId}
        title="Delete Maintenance Window"
        message="Are you sure you want to delete this maintenance schedule?"
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />
    </div>
  );
}
