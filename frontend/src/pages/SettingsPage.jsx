import React, { useState, useEffect } from 'react';
import { Card, Form, Button, Row, Col, Table, Badge, Spinner, Alert } from '../components/bic';
import { toast } from '../components/bic/Notifications';
import { MdSave, MdSend, MdEmail, MdSettings, MdHistory, MdRefresh } from 'react-icons/md';
import { get, put, post } from '../api/client';
import dayjs from 'dayjs';

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    default_monitoring_interval: '15',
    default_ping_timeout: '2',
    default_failure_threshold: '3',
    default_recovery_threshold: '2',
    latency_warning_threshold: '100',
    latency_critical_threshold: '250',
    data_retention_raw_days: '7',
    data_retention_aggregate_days: '30',
    app_timezone: 'Asia/Jakarta',
    // Email-only notification policy
    email_notifications_enabled: 'true',
    down_notifications_enabled: 'true',
    recovery_notifications_enabled: 'true',
    degraded_notifications_enabled: 'true',
    maintenance_suppression_enabled: 'true',
    parent_down_suppression_enabled: 'true',
    critical_reminder_1_minutes: '15',
    critical_reminder_2_minutes: '60',
    critical_reminder_repeat_hours: '4',
    high_reminder_1_minutes: '30',
    high_reminder_2_minutes: '120',
    high_reminder_repeat_hours: '6',
    // SMTP
    smtp_enabled: 'false',
    smtp_host: '',
    smtp_port: '587',
    smtp_encryption: 'TLS',
    smtp_user: '',
    smtp_password: '',
    smtp_from_email: 'nms-alert@local',
    smtp_sender_name: 'NMS',
    smtp_reply_to: '',
    smtp_to_emails: ''
  });

  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState([]);
  const [loadingLogs, setLoadingLogs] = useState(false);

  // Testing states
  const [testingSmtp, setTestingSmtp] = useState(false);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const res = await get('/settings');
      if (Array.isArray(res.data)) {
        const mapped = {};
        res.data.forEach(item => {
          mapped[item.key] = item.value || '';
        });
        setSettings(prev => ({ ...prev, ...mapped }));
      }
    } catch (error) {
      console.error('Error loading settings', error);
      toast.error('Failed to load system settings');
    } finally {
      setLoading(false);
    }
  };

  const fetchNotificationLogs = async () => {
    try {
      setLoadingLogs(true);
      const res = await get('/notifications/logs?page=1&page_size=10');
      setLogs(res.data.data || []);
    } catch (error) {
      console.error('Error loading notification logs', error);
    } finally {
      setLoadingLogs(false);
    }
  };

  useEffect(() => {
    fetchSettings();
    fetchNotificationLogs();
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (checked ? 'true' : 'false') : value
    }));
  };

  const persistSettings = async () => {
    const payload = {
      settings: Object.entries(settings).map(([key, value]) => ({
        key,
        value: String(value)
      }))
    };
    await put('/settings', payload);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await persistSettings();
      toast.success('System settings saved successfully!');
    } catch (error) {
      console.error('Error saving settings', error);
      toast.error(error.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleTestEmail = async () => {
    const recipient = settings.smtp_to_emails.split(',').map(value => value.trim()).find(Boolean);
    if (!settings.smtp_host || !recipient) {
      toast.error('SMTP host and recipient email address must be configured.');
      return;
    }
    setTestingSmtp(true);
    try {
      await persistSettings();
      const res = await post('/notifications/test', {
        channel: 'EMAIL',
        custom_message: 'Manual SMTP email test from NMS Settings interface'
      });
      toast.success(res.data.message || 'Test email sent successfully!');
      fetchNotificationLogs();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Email test failed');
    } finally {
      setTestingSmtp(false);
    }
  };

  if (loading) {
    return (
      <div className="bic-text-center bic-py-10">
        <Spinner />
        <p className="bic-mt-2 bic-text-secondary">Loading settings...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="bic-page-header">
        <div>
          <h1 className="bic-page-title bic-flex bic-items-center bic-gap-2">
            <MdSettings /> System Settings & Notifications
          </h1>
          <p className="bic-page-subtitle">Configure monitoring parameters, alert channels, and retention rules.</p>
        </div>
      </div>

      <Form onSubmit={handleSave}>
        <Row className="bic-gap-6 bic-mb-6">
          {/* General Monitoring Thresholds */}
          <Col lg={6}>
            <Card className="bic-h-full">
              <Card.Header>
                <h2 className="bic-section-title bic-mb-0">Monitoring Engine Thresholds</h2>
              </Card.Header>
              <Card.Body>
                <Row>
                  <Col sm={6}>
                    <Form.Group>
                      <Form.Label>Default Interval (seconds)</Form.Label>
                      <Form.Control
                        type="number"
                        name="default_monitoring_interval"
                        value={settings.default_monitoring_interval}
                        onChange={handleChange}
                        required
                      />
                    </Form.Group>
                  </Col>
                  <Col sm={6}>
                    <Form.Group>
                      <Form.Label>Ping Timeout (seconds)</Form.Label>
                      <Form.Control
                        type="number"
                        name="default_ping_timeout"
                        value={settings.default_ping_timeout}
                        onChange={handleChange}
                        required
                      />
                    </Form.Group>
                  </Col>
                  <Col sm={6}>
                    <Form.Group>
                      <Form.Label>Failure Threshold (Checks before DOWN)</Form.Label>
                      <Form.Control
                        type="number"
                        name="default_failure_threshold"
                        value={settings.default_failure_threshold}
                        onChange={handleChange}
                        required
                      />
                    </Form.Group>
                  </Col>
                  <Col sm={6}>
                    <Form.Group>
                      <Form.Label>Recovery Threshold (Checks before UP)</Form.Label>
                      <Form.Control
                        type="number"
                        name="default_recovery_threshold"
                        value={settings.default_recovery_threshold}
                        onChange={handleChange}
                        required
                      />
                    </Form.Group>
                  </Col>
                  <Col sm={6}>
                    <Form.Group>
                      <Form.Label>Latency Warning (ms)</Form.Label>
                      <Form.Control
                        type="number"
                        name="latency_warning_threshold"
                        value={settings.latency_warning_threshold}
                        onChange={handleChange}
                      />
                    </Form.Group>
                  </Col>
                  <Col sm={6}>
                    <Form.Group>
                      <Form.Label>Latency Critical (ms)</Form.Label>
                      <Form.Control
                        type="number"
                        name="latency_critical_threshold"
                        value={settings.latency_critical_threshold}
                        onChange={handleChange}
                      />
                    </Form.Group>
                  </Col>
                  <Col sm={12}>
                    <Form.Group>
                      <Form.Label>Application Timezone</Form.Label>
                      <Form.Select name="app_timezone" value={settings.app_timezone} onChange={handleChange}>
                        <option value="Asia/Jakarta">Asia/Jakarta (WIB)</option>
                        <option value="UTC">UTC</option>
                        <option value="America/New_York">America/New_York (EST)</option>
                        <option value="Europe/London">Europe/London (GMT)</option>
                      </Form.Select>
                    </Form.Group>
                  </Col>
                  <Col sm={12}>
                    <div className="bic-inset bic-mt-2">
                      <p className="bic-text-sm bic-text-secondary bic-mb-2">Email notification policy</p>
                      <Row>
                        <Col sm={6}>
                          <Form.Check type="switch" id="email-notifications-switch" name="email_notifications_enabled" label="Email alerts enabled" checked={settings.email_notifications_enabled === 'true'} onChange={handleChange} />
                          <Form.Check type="switch" id="down-notifications-switch" name="down_notifications_enabled" label="DOWN alerts" checked={settings.down_notifications_enabled === 'true'} onChange={handleChange} />
                          <Form.Check type="switch" id="recovery-notifications-switch" name="recovery_notifications_enabled" label="Recovery alerts" checked={settings.recovery_notifications_enabled === 'true'} onChange={handleChange} />
                        </Col>
                        <Col sm={6}>
                          <Form.Check type="switch" id="degraded-notifications-switch" name="degraded_notifications_enabled" label="Degraded / warning alerts" checked={settings.degraded_notifications_enabled === 'true'} onChange={handleChange} />
                          <Form.Check type="switch" id="maintenance-suppression-switch" name="maintenance_suppression_enabled" label="Suppress maintenance alerts" checked={settings.maintenance_suppression_enabled === 'true'} onChange={handleChange} />
                          <Form.Check type="switch" id="parent-suppression-switch" name="parent_down_suppression_enabled" label="Suppress child alerts when parent is down" checked={settings.parent_down_suppression_enabled === 'true'} onChange={handleChange} />
                        </Col>
                      </Row>
                      <p className="bic-text-sm bic-text-secondary bic-mt-4 bic-mb-2">Open incident reminder schedule</p>
                      <Row>
                        <Col sm={4}><Form.Group><Form.Label>Critical first (min)</Form.Label><Form.Control type="number" min="1" name="critical_reminder_1_minutes" value={settings.critical_reminder_1_minutes} onChange={handleChange} /></Form.Group></Col>
                        <Col sm={4}><Form.Group><Form.Label>Critical second (min)</Form.Label><Form.Control type="number" min="1" name="critical_reminder_2_minutes" value={settings.critical_reminder_2_minutes} onChange={handleChange} /></Form.Group></Col>
                        <Col sm={4}><Form.Group><Form.Label>Critical repeat (hours)</Form.Label><Form.Control type="number" min="1" name="critical_reminder_repeat_hours" value={settings.critical_reminder_repeat_hours} onChange={handleChange} /></Form.Group></Col>
                        <Col sm={4}><Form.Group><Form.Label>High first (min)</Form.Label><Form.Control type="number" min="1" name="high_reminder_1_minutes" value={settings.high_reminder_1_minutes} onChange={handleChange} /></Form.Group></Col>
                        <Col sm={4}><Form.Group><Form.Label>High second (min)</Form.Label><Form.Control type="number" min="1" name="high_reminder_2_minutes" value={settings.high_reminder_2_minutes} onChange={handleChange} /></Form.Group></Col>
                        <Col sm={4}><Form.Group><Form.Label>High repeat (hours)</Form.Label><Form.Control type="number" min="1" name="high_reminder_repeat_hours" value={settings.high_reminder_repeat_hours} onChange={handleChange} /></Form.Group></Col>
                      </Row>
                    </div>
                  </Col>
                </Row>
              </Card.Body>
            </Card>
          </Col>

          <Col lg={6}>
            {/* Email SMTP Channel */}
            <Card>
              <Card.Header>
                <h2 className="bic-section-title bic-mb-0 bic-flex bic-items-center bic-gap-2">
                  <MdEmail /> Email (SMTP) Alerts
                </h2>
                <Form.Check
                  type="switch"
                  id="smtp-switch"
                  name="smtp_enabled"
                  label="Enabled"
                  checked={settings.smtp_enabled === 'true'}
                  onChange={handleChange}
                />
              </Card.Header>
              <Card.Body>
                <Row className="bic-gap-2 bic-mb-4">
                  <Col sm={8}>
                    <Form.Group>
                      <Form.Label>SMTP Host</Form.Label>
                      <Form.Control
                        type="text"
                        name="smtp_host"
                        placeholder="smtp.gmail.com / mail.company.com"
                        value={settings.smtp_host}
                        onChange={handleChange}
                      />
                    </Form.Group>
                  </Col>
                  <Col sm={4}>
                    <Form.Group>
                      <Form.Label>Port</Form.Label>
                      <Form.Control
                        type="number"
                        name="smtp_port"
                        value={settings.smtp_port}
                        onChange={handleChange}
                      />
                    </Form.Group>
                  </Col>
                </Row>
                <Row className="bic-gap-2 bic-mb-4">
                  <Col sm={6}>
                    <Form.Group>
                      <Form.Label>Encryption</Form.Label>
                      <Form.Select name="smtp_encryption" value={settings.smtp_encryption} onChange={handleChange}>
                        <option value="TLS">STARTTLS (TLS)</option>
                        <option value="SSL">SSL/TLS</option>
                        <option value="NONE">None</option>
                      </Form.Select>
                    </Form.Group>
                  </Col>
                  <Col sm={6}>
                    <Form.Group>
                      <Form.Label>Sender Name</Form.Label>
                      <Form.Control type="text" name="smtp_sender_name" value={settings.smtp_sender_name} onChange={handleChange} />
                    </Form.Group>
                  </Col>
                </Row>
                <Row className="bic-gap-2 bic-mb-4">
                  <Col sm={6}>
                    <Form.Group>
                      <Form.Label>SMTP User</Form.Label>
                      <Form.Control
                        type="text"
                        name="smtp_user"
                        value={settings.smtp_user}
                        onChange={handleChange}
                      />
                    </Form.Group>
                  </Col>
                  <Col sm={6}>
                    <Form.Group>
                      <Form.Label>SMTP Password</Form.Label>
                      <Form.Control
                        type="password"
                        name="smtp_password"
                        value={settings.smtp_password}
                        onChange={handleChange}
                      />
                    </Form.Group>
                  </Col>
                </Row>
                <Form.Group className="bic-mb-4">
                  <Form.Label>Reply-To Email (optional)</Form.Label>
                  <Form.Control type="email" name="smtp_reply_to" value={settings.smtp_reply_to} onChange={handleChange} />
                </Form.Group>
                <Form.Group className="bic-mb-4">
                  <Form.Label>From Email</Form.Label>
                  <Form.Control
                    type="email"
                    name="smtp_from_email"
                    placeholder="your-account@gmail.com"
                    value={settings.smtp_from_email}
                    onChange={handleChange}
                  />
                  <Form.Text className="bic-text-secondary">Use the same Gmail address as the authenticated SMTP account.</Form.Text>
                </Form.Group>
                <Form.Group className="bic-mb-4">
                  <Form.Label>Recipient Emails (Comma-separated)</Form.Label>
                  <Form.Control
                    type="text"
                    name="smtp_to_emails"
                    placeholder="noc@company.com, admin@company.com"
                    value={settings.smtp_to_emails}
                    onChange={handleChange}
                  />
                </Form.Group>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleTestEmail}
                  disabled={testingSmtp || settings.smtp_enabled !== 'true' || !settings.smtp_host || !settings.smtp_to_emails.trim()}
                >
                  <MdSend className="bic-mr-1" />
                  {testingSmtp ? 'Sending...' : 'Send Test Email'}
                </Button>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        <div className="bic-flex bic-justify-end bic-mb-6">
          <Button variant="primary" size="lg" type="submit" disabled={saving}>
            <MdSave className="bic-mr-2" />
            {saving ? 'Saving Changes...' : 'Save Configuration'}
          </Button>
        </div>
      </Form>

      {/* Recent Notification Logs */}
      <Card className="bic-mb-10">
        <Card.Header>
          <h2 className="bic-section-title bic-mb-0 bic-flex bic-items-center bic-gap-2">
            <MdHistory /> Notification Activity Log
          </h2>
          <Button variant="secondary" size="sm" onClick={fetchNotificationLogs} disabled={loadingLogs}>
            <MdRefresh /> Refresh Logs
          </Button>
        </Card.Header>
        <Card.Body className="bic-p-0">
          <Table responsive hover className="bic-mb-0">
            <thead>
              <tr>
                <th>Channel</th>
                <th>Event Type</th>
                <th>Recipient</th>
                <th>Status</th>
                <th>Sent At</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {logs.length > 0 ? (
                logs.map((log) => (
                  <tr key={log.id}>
                    <td>
                      <Badge bg="info">
                        {log.channel}
                      </Badge>
                    </td>
                    <td><strong className="bic-text-sm">{log.event_type}</strong></td>
                    <td className="bic-text-sm"><code>{log.recipient}</code></td>
                    <td>
                      <Badge bg={log.status === 'SENT' ? 'success' : (log.status === 'FAILED' ? 'danger' : 'info')}>
                        {log.status}
                      </Badge>
                    </td>
                    <td className="bic-text-sm bic-text-secondary">{dayjs(log.sent_at).format('YYYY-MM-DD HH:mm:ss')}</td>
                    <td className="bic-text-sm bic-text-secondary bic-table-note">
                      {log.error_message ? (
                        <span className="bic-text-danger">{log.error_message}</span>
                      ) : (
                        <span>{log.subject || 'Message delivered'}</span>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="6" className="bic-empty">
                    No notification activities logged yet.
                  </td>
                </tr>
              )}
            </tbody>
          </Table>
        </Card.Body>
      </Card>
    </div>
  );
}
