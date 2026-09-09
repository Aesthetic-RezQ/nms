import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button, Table, Form, Row, Col, Card, Badge, Modal, Alert, Spinner } from '../components/bic';
import { MdAdd, MdDelete, MdEdit, MdFileDownload, MdFileUpload, MdVisibility, MdCheckCircle, MdError } from 'react-icons/md';
import { toast } from '../components/bic/Notifications';
import { get, del, post } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { DEVICE_STATUSES } from '../utils/constants';
import StatusBadge from '../components/common/StatusBadge';
import ConfirmDialog from '../components/common/ConfirmDialog';
import dayjs from 'dayjs';

export default function DevicesPage() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [categories, setCategories] = useState([]);
  const [groups, setGroups] = useState([]);
  const [locations, setLocations] = useState([]);
  
  const [filters, setFilters] = useState({ status: '', category_id: '', group_id: '', location_id: '', search: '' });
  const [deleteId, setDeleteId] = useState(null);
  
  // CSV Import State
  const [showImportModal, setShowImportModal] = useState(false);
  const [importFile, setImportFile] = useState(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);

  const navigate = useNavigate();
  const { isAdmin } = useAuth();

  useEffect(() => {
    fetchMetadata();
    fetchDevices();
  }, []);

  const fetchMetadata = async () => {
    try {
      const [catRes, grpRes, locRes] = await Promise.all([
        get('/categories'), get('/groups'), get('/locations')
      ]);
      setCategories(catRes.data);
      setGroups(grpRes.data);
      setLocations(locRes.data);
    } catch (error) {
      console.error('Error fetching metadata', error);
    }
  };

  const fetchDevices = async () => {
    setLoading(true);
    try {
      let query = new URLSearchParams();
      if (filters.status) query.append('status', filters.status);
      if (filters.category_id) query.append('category_id', filters.category_id);
      if (filters.group_id) query.append('group_id', filters.group_id);
      if (filters.location_id) query.append('location_id', filters.location_id);
      if (filters.search) query.append('search', filters.search);
      query.append('page_size', '100');

      const res = await get(`/devices?${query.toString()}`);
      setDevices(res.data.data || res.data.items || res.data || []);
    } catch (error) {
      toast.error('Failed to load devices');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const handleApplyFilters = (e) => {
    e.preventDefault();
    fetchDevices();
  };

  const handleExportCSV = async () => {
    try {
      const res = await get('/devices/export', { responseType: 'text' });
      const blob = new Blob([res.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `devices_export_${dayjs().format('YYYYMMDD_HHmmss')}.csv`;
      a.click();
      toast.success('Device list exported');
    } catch (err) {
      toast.error('Failed to export devices');
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      setImportFile(e.target.files[0]);
      setImportResult(null);
    }
  };

  const handleExecuteImport = async () => {
    if (!importFile) return;
    setImporting(true);
    setImportResult(null);
    try {
      const formData = new FormData();
      formData.append('file', importFile);

      const res = await post('/devices/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setImportResult(res.data);
      toast.success(`Import completed: ${res.data.created} devices imported.`);
      fetchDevices();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'CSV import failed');
    } finally {
      setImporting(false);
    }
  };

  const handleDelete = async () => {
    try {
      await del(`/devices/${deleteId}`);
      toast.success('Device deleted successfully');
      fetchDevices();
    } catch (error) {
      toast.error('Failed to delete device');
    } finally {
      setDeleteId(null);
    }
  };

  return (
    <div>
      <div className="bic-page-header">
        <div>
          <h1 className="bic-page-title">Device Management</h1>
          <p className="bic-page-subtitle">Register, configure, and inspect LAN network assets.</p>
        </div>
        <div className="bic-toolbar">
          <Button variant="secondary" onClick={handleExportCSV}>
            <MdFileDownload className="bic-mr-1" /> Export CSV
          </Button>
          {isAdmin && (
            <>
              <Button variant="secondary" onClick={() => { setShowImportModal(true); setImportResult(null); setImportFile(null); }}>
                <MdFileUpload className="bic-mr-1" /> Import CSV
              </Button>
              <Button variant="primary" onClick={() => navigate('/devices/new')}>
                <MdAdd className="bic-mr-1" /> Add Device
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Filters Card */}
      <Card className="bic-mb-6">
        <Card.Body>
          <Form onSubmit={handleApplyFilters}>
            <Row className="bic-gap-2">
              <Col lg={2} md={4} sm={6}>
                <Form.Select aria-label="Filter by status" name="status" value={filters.status} onChange={handleFilterChange}>
                  <option value="">All Statuses</option>
                  {DEVICE_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                </Form.Select>
              </Col>
              <Col lg={2} md={4} sm={6}>
                <Form.Select aria-label="Filter by category" name="category_id" value={filters.category_id} onChange={handleFilterChange}>
                  <option value="">All Categories</option>
                  {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </Form.Select>
              </Col>
              <Col lg={2} md={4} sm={6}>
                <Form.Select aria-label="Filter by group" name="group_id" value={filters.group_id} onChange={handleFilterChange}>
                  <option value="">All Groups</option>
                  {groups.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
                </Form.Select>
              </Col>
              <Col lg={2} md={4} sm={6}>
                <Form.Select aria-label="Filter by location" name="location_id" value={filters.location_id} onChange={handleFilterChange}>
                  <option value="">All Locations</option>
                  {locations.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
                </Form.Select>
              </Col>
              <Col lg={3} md={6}>
                <Form.Control 
                  name="search" 
                  aria-label="Search devices"
                  placeholder="Search name, IP, hostname..." 
                  value={filters.search} 
                  onChange={handleFilterChange} 
                />
              </Col>
              <Col lg={1} md={2}>
                <Button type="submit" variant="secondary" className="bic-w-full">Filter</Button>
              </Col>
            </Row>
          </Form>
        </Card.Body>
      </Card>

      {/* Devices Table */}
      <Card>
        <Table responsive hover className="bic-mb-0">
          <thead>
            <tr>
              <th className="bic-pl-4">Status</th>
              <th>Device Name</th>
              <th>IP Address</th>
              <th>Category</th>
              <th>Group</th>
              <th>Location</th>
              <th>Latency</th>
              <th>Last Check</th>
              <th className="bic-text-right bic-pr-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="9" className="bic-empty">Loading devices...</td></tr>
            ) : devices.length === 0 ? (
              <tr><td colSpan="9" className="bic-empty">No devices found matching filter.</td></tr>
            ) : (
              devices.map(dev => (
                <tr key={dev.id}>
                  <td className="bic-pl-4">
                    <StatusBadge status={dev.current_status || dev.status} />
                  </td>
                  <td>
                    <Link to={`/devices/${dev.id}`} className="bic-font-semibold bic-text-primary">
                      {dev.device_name || dev.name}
                    </Link>
                    {dev.hostname && <div className="bic-text-secondary bic-text-sm">{dev.hostname}</div>}
                  </td>
                  <td><code>{dev.ip_address}</code></td>
                  <td>{dev.category_name || dev.category?.name || '—'}</td>
                  <td>{dev.group_name || dev.group?.name || '—'}</td>
                  <td>{dev.location_name || dev.location?.name || '—'}</td>
                  <td>
                    {dev.current_latency !== null && dev.current_latency !== undefined ? (
                      <span className={`bic-font-semibold ${dev.current_latency > 100 ? 'bic-text-warning' : 'bic-text-success'}`}>
                        {dev.current_latency} ms
                      </span>
                    ) : (
                      <span className="bic-text-secondary">—</span>
                    )}
                  </td>
                  <td className="bic-text-sm bic-text-secondary">
                    {dev.last_check ? dayjs(dev.last_check).format('YYYY-MM-DD HH:mm') : 'Never'}
                  </td>
                  <td className="bic-text-right bic-pr-4">
                    <div className="bic-button-group bic-button-group-sm">
                      <Link to={`/devices/${dev.id}`} className="bic-btn bic-btn-secondary" title="View Analytics">
                        <MdVisibility />
                      </Link>
                      {isAdmin && (
                        <>
                          <Link to={`/devices/${dev.id}/edit`} className="bic-btn bic-btn-secondary" title="Edit Configuration">
                            <MdEdit />
                          </Link>
                          <Button variant="danger" onClick={() => setDeleteId(dev.id)} title="Delete Device">
                            <MdDelete />
                          </Button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </Table>
      </Card>

      {/* CSV Bulk Import Modal (PRD §47) */}
      <Modal show={showImportModal} onHide={() => setShowImportModal(false)} size="lg" centered>
        <Modal.Header closeButton>
          <Modal.Title>Bulk Import Devices from CSV</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p className="bic-text-secondary bic-text-sm">
            Upload a CSV file containing columns: <code>device_name, ip_address, hostname, category, group, location, vlan_id, subnet</code>.
          </p>

          <Form.Group className="bic-mb-4">
            <Form.Label>Select CSV File</Form.Label>
            <Form.Control type="file" accept=".csv" onChange={handleFileSelect} />
          </Form.Group>

          {importResult && (
            <Alert variant={importResult.created > 0 ? "success" : "warning"} className="bic-mt-4">
              <div className="bic-font-semibold bic-mb-1">
                Import Summary: {importResult.created} Imported | {importResult.total - importResult.created} Skipped / Errors
              </div>
              {importResult.errors && importResult.errors.length > 0 && (
                <div className="bic-text-sm bic-mt-2 bic-scroll-area-sm">
                  <div className="bic-text-danger bic-font-semibold">Issues Encountered:</div>
                  <ul className="bic-mb-0 bic-pl-4">
                    {importResult.errors.map((err, idx) => (
                      <li key={idx}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}
            </Alert>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowImportModal(false)}>Close</Button>
          <Button variant="primary" onClick={handleExecuteImport} disabled={!importFile || importing}>
            {importing ? <><Spinner size="sm" className="bic-mr-1" /> Importing...</> : 'Start Import'}
          </Button>
        </Modal.Footer>
      </Modal>

      <ConfirmDialog
        show={!!deleteId}
        title="Delete Device"
        message="Are you sure you want to delete this device? Historical monitoring results and active incidents will be removed."
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />
    </div>
  );
}
