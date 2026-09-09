import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Form, Button, Card, Row, Col, Spinner } from '../components/bic';
import { toast } from '../components/bic/Notifications';
import { get, post, put } from '../api/client';

export default function DeviceFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = !!id;

  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [metadata, setMetadata] = useState({ categories: [], groups: [], locations: [], devices: [] });
  
  const [formData, setFormData] = useState({
    device_name: '',
    ip_address: '',
    hostname: '',
    description: '',
    category_id: '',
    group_id: '',
    location_id: '',
    vlan_id: '',
    vlan_name: '',
    subnet: '',
    parent_device_id: '',
    monitoring_enabled: true,
    monitoring_interval: '',
    ping_timeout: '',
    failure_threshold: '',
    recovery_threshold: ''
  });

  const [errors, setErrors] = useState({});

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [cat, grp, loc, devs] = await Promise.all([
          get('/categories'),
          get('/groups'),
          get('/locations'),
          get('/devices?page_size=1000')
        ]);
        setMetadata({
          categories: Array.isArray(cat.data) ? cat.data : (cat.data?.data || []),
          groups: Array.isArray(grp.data) ? grp.data : (grp.data?.data || []),
          locations: Array.isArray(loc.data) ? loc.data : (loc.data?.data || []),
          devices: devs.data.data || devs.data.items || (Array.isArray(devs.data) ? devs.data : [])
        });

        if (isEdit) {
          const res = await get(`/devices/${id}`);
          const d = res.data;
          setFormData({
            device_name: d.device_name || '',
            ip_address: d.ip_address || '',
            hostname: d.hostname || '',
            description: d.description || '',
            category_id: d.category_id || '',
            group_id: d.group_id || '',
            location_id: d.location_id || '',
            vlan_id: d.vlan_id || '',
            vlan_name: d.vlan_name || '',
            subnet: d.subnet || '',
            parent_device_id: d.parent_device_id || '',
            monitoring_enabled: d.monitoring_enabled !== false,
            monitoring_interval: d.monitoring_interval || '',
            ping_timeout: d.ping_timeout || '',
            failure_threshold: d.failure_threshold || '',
            recovery_threshold: d.recovery_threshold || ''
          });
        }
      } catch (err) {
        console.error('Failed to load device form data', err);
        toast.error('Failed to load metadata');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id, isEdit]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.device_name.trim()) newErrors.device_name = 'Device name is required';
    if (!formData.ip_address.trim()) {
      newErrors.ip_address = 'IP Address is required';
    } else if (!/^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/.test(formData.ip_address.trim())) {
      newErrors.ip_address = 'Invalid IPv4 address format (e.g. 192.168.1.1)';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    
    setSaving(true);
    try {
      const payload = {
        device_name: formData.device_name.trim(),
        ip_address: formData.ip_address.trim(),
        hostname: formData.hostname.trim() || null,
        description: formData.description.trim() || null,
        category_id: formData.category_id ? parseInt(formData.category_id, 10) : null,
        group_id: formData.group_id ? parseInt(formData.group_id, 10) : null,
        location_id: formData.location_id ? parseInt(formData.location_id, 10) : null,
        vlan_id: formData.vlan_id ? parseInt(formData.vlan_id, 10) : null,
        vlan_name: formData.vlan_name.trim() || null,
        subnet: formData.subnet.trim() || null,
        parent_device_id: formData.parent_device_id || null,
        monitoring_enabled: !!formData.monitoring_enabled,
        monitoring_interval: formData.monitoring_interval ? parseInt(formData.monitoring_interval, 10) : null,
        ping_timeout: formData.ping_timeout ? parseInt(formData.ping_timeout, 10) : null,
        failure_threshold: formData.failure_threshold ? parseInt(formData.failure_threshold, 10) : null,
        recovery_threshold: formData.recovery_threshold ? parseInt(formData.recovery_threshold, 10) : null
      };

      if (isEdit) {
        await put(`/devices/${id}`, payload);
        toast.success('Device updated successfully');
      } else {
        await post('/devices', payload);
        toast.success('Device created successfully');
      }
      navigate('/devices');
    } catch (err) {
      console.error('Error saving device', err);
      toast.error(err.response?.data?.detail || err.response?.data?.error?.message || 'Failed to save device');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="bic-text-center bic-p-10"><Spinner /></div>;

  return (
    <div>
      <div className="bic-page-header"><h1 className="bic-page-title">{isEdit ? 'Edit Device' : 'Add Device'}</h1></div>
      
      <Form onSubmit={handleSubmit}>
        <Row>
          <Col lg={8}>
            <Card className="bic-mb-6">
              <Card.Header>
                <h2 className="bic-section-title bic-mb-0">Basic Information</h2>
              </Card.Header>
              <Card.Body>
                <Row>
                  <Col md={6}>
                    <Form.Group>
                      <Form.Label>Device Name *</Form.Label>
                      <Form.Control 
                        name="device_name" 
                        placeholder="e.g. Core-Router-01"
                        value={formData.device_name} 
                        onChange={handleChange} 
                        isInvalid={!!errors.device_name} 
                      />
                      <Form.Control.Feedback type="invalid">{errors.device_name}</Form.Control.Feedback>
                    </Form.Group>
                  </Col>
                  <Col md={6}>
                    <Form.Group>
                      <Form.Label>IP Address *</Form.Label>
                      <Form.Control 
                        name="ip_address" 
                        placeholder="e.g. 192.168.1.1"
                        value={formData.ip_address} 
                        onChange={handleChange} 
                        isInvalid={!!errors.ip_address} 
                      />
                      <Form.Control.Feedback type="invalid">{errors.ip_address}</Form.Control.Feedback>
                    </Form.Group>
                  </Col>
                  <Col md={6}>
                    <Form.Group>
                      <Form.Label>Hostname</Form.Label>
                      <Form.Control 
                        name="hostname" 
                        placeholder="e.g. router01.local"
                        value={formData.hostname} 
                        onChange={handleChange} 
                      />
                    </Form.Group>
                  </Col>
                  <Col md={6}>
                    <Form.Group>
                      <Form.Label>Subnet</Form.Label>
                      <Form.Control 
                        name="subnet" 
                        placeholder="e.g. 192.168.1.0/24" 
                        value={formData.subnet} 
                        onChange={handleChange} 
                      />
                    </Form.Group>
                  </Col>
                  <Col md={12}>
                    <Form.Group>
                      <Form.Label>Description</Form.Label>
                      <Form.Control 
                        as="textarea" 
                        rows={2} 
                        name="description" 
                        placeholder="Optional device description or notes"
                        value={formData.description} 
                        onChange={handleChange} 
                      />
                    </Form.Group>
                  </Col>
                </Row>
              </Card.Body>
            </Card>

            <Card className="bic-mb-6">
              <Card.Header>
                <h2 className="bic-section-title bic-mb-0">Classification & Location</h2>
              </Card.Header>
              <Card.Body>
                <Row>
                  <Col md={4}>
                    <Form.Group>
                      <Form.Label>Category</Form.Label>
                      <Form.Select name="category_id" value={formData.category_id || ''} onChange={handleChange}>
                        <option value="">None</option>
                        {metadata.categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                      </Form.Select>
                    </Form.Group>
                  </Col>
                  <Col md={4}>
                    <Form.Group>
                      <Form.Label>Group</Form.Label>
                      <Form.Select name="group_id" value={formData.group_id || ''} onChange={handleChange}>
                        <option value="">None</option>
                        {metadata.groups.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
                      </Form.Select>
                    </Form.Group>
                  </Col>
                  <Col md={4}>
                    <Form.Group>
                      <Form.Label>Location</Form.Label>
                      <Form.Select name="location_id" value={formData.location_id || ''} onChange={handleChange}>
                        <option value="">None</option>
                        {metadata.locations.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
                      </Form.Select>
                    </Form.Group>
                  </Col>
                  <Col md={6}>
                    <Form.Group>
                      <Form.Label>VLAN ID</Form.Label>
                      <Form.Control type="number" name="vlan_id" placeholder="e.g. 10" value={formData.vlan_id} onChange={handleChange} />
                    </Form.Group>
                  </Col>
                  <Col md={6}>
                    <Form.Group>
                      <Form.Label>VLAN Name</Form.Label>
                      <Form.Control name="vlan_name" placeholder="e.g. MANAGEMENT" value={formData.vlan_name} onChange={handleChange} />
                    </Form.Group>
                  </Col>
                  <Col md={12}>
                    <Form.Group>
                      <Form.Label>Parent Device (Upstream Dependency)</Form.Label>
                      <Form.Select name="parent_device_id" value={formData.parent_device_id || ''} onChange={handleChange}>
                        <option value="">None (Independent Root)</option>
                        {metadata.devices.filter(d => d.id !== id).map(d => (
                          <option key={d.id} value={d.id}>{d.device_name} ({d.ip_address})</option>
                        ))}
                      </Form.Select>
                    </Form.Group>
                  </Col>
                </Row>
              </Card.Body>
            </Card>
          </Col>

          <Col lg={4}>
            <Card className="bic-mb-6">
              <Card.Header>
                <h2 className="bic-section-title bic-mb-0">Monitoring Settings</h2>
              </Card.Header>
              <Card.Body>
                <Form.Group className="bic-mb-4">
                  <Form.Check 
                    type="switch" 
                    id="monitoring-switch" 
                    label="Enable Ping Monitoring" 
                    name="monitoring_enabled" 
                    checked={formData.monitoring_enabled} 
                    onChange={handleChange} 
                  />
                </Form.Group>
                <Form.Group className="bic-mb-4">
                  <Form.Label>Interval (seconds)</Form.Label>
                  <Form.Control type="number" name="monitoring_interval" placeholder="Default: 15" value={formData.monitoring_interval} onChange={handleChange} />
                </Form.Group>
                <Form.Group className="bic-mb-4">
                  <Form.Label>Ping Timeout (seconds)</Form.Label>
                  <Form.Control type="number" name="ping_timeout" placeholder="Default: 2" value={formData.ping_timeout} onChange={handleChange} />
                </Form.Group>
                <Form.Group className="bic-mb-4">
                  <Form.Label>Failure Threshold (pings)</Form.Label>
                  <Form.Control type="number" name="failure_threshold" placeholder="Default: 3" value={formData.failure_threshold} onChange={handleChange} />
                </Form.Group>
                <Form.Group className="bic-mb-4">
                  <Form.Label>Recovery Threshold (pings)</Form.Label>
                  <Form.Control type="number" name="recovery_threshold" placeholder="Default: 2" value={formData.recovery_threshold} onChange={handleChange} />
                </Form.Group>
              </Card.Body>
            </Card>
          </Col>
        </Row>
        
        <div className="bic-flex bic-gap-2 bic-mb-10">
          <Button variant="primary" type="submit" disabled={saving}>
            {saving ? <Spinner size="sm" className="bic-mr-2" /> : null}
            Save Device
          </Button>
          <Button variant="secondary" onClick={() => navigate('/devices')} disabled={saving}>
            Cancel
          </Button>
        </div>
      </Form>
    </div>
  );
}
