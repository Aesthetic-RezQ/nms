import React, { useState, useEffect } from 'react';
import { Card, Form, Button, Row, Col, Table, Badge, Spinner, Alert } from '../components/bic';
import { toast } from '../components/bic/Notifications';
import { MdSave, MdSend, MdEmail, MdSendToMobile, MdSettings, MdHistory, MdRefresh } from 'react-icons/md';
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
    // Telegram
    telegram_enabled: 'false',
    telegram_bot_token: '',
    telegram_chat_id: '',
    // SMTP
    smtp_enabled: 'false',
    smtp_host: '',
    smtp_port: '587',
    smtp_user: '',
    smtp_password: '',
    smtp_from_email: 'nms-alert@local',
    smtp_to_emails: ''
  });

  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState([]);
  const [loadingLogs, setLoadingLogs] = useState(false);

  // Testing states
  const [testingTg, setTestingTg] = useState(false);
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

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        settings: Object.entries(settings).map(([key, value]) => ({
          key,
          value: String(value)
        }))
      };
      await put('/settings', payload);
      toast.success('System settings saved successfully!');
    } catch (error) {
      console.error('Error saving settings', error);
      toast.error(error.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleTestTelegram = async () => {
    setTestingTg(true);
    try {
      const res = await post('/notifications/test', {
        channel: 'TELEGRAM',
        custom_message: 'Manual test from NMS Settings interface'
      });
      toast.success(res.data.message || 'Telegram test sent successfully!');
      fetchNotificationLogs();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Telegram test failed');
    } finally {
      setTestingTg(false);
    }
  };

  const handleTestEmail = async () => {
    setTestingSmtp(true);
    try {
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
                </Row>
              </Card.Body>
            </Card>
          </Col>

          {/* Telegram Notification Channel */}
          <Col lg={6}>
            <Card className="bic-mb-6">
              <Card.Header>
                <h2 className="bic-section-title bic-mb-0 bic-flex bic-items-center bic-gap-2">
                  <MdSendToMobile className="bic-text-brand" /> Telegram Bot Alerts
                </h2>
                <Form.Check
                  type="switch"
                  id="tg-switch"
                  name="telegram_enabled"
                  label="Enabled"
                  checked={settings.telegram_enabled === 'true'}
                  onChange={handleChange}
                />
              </Card.Header>
              <Card.Body>
                <Form.Group className="bic-mb-4">
                  <Form.Label>Telegram Bot Token</Form.Label>
                  <Form.Control
                    type="password"
                    name="telegram_bot_token"
                    placeholder="e.g. 123456789:ABCdefGhIJKlmNoPQRstuVwxyZ"
                    value={settings.telegram_bot_token}
                    onChange={handleChange}
                  />
                  <Form.Text className="bic-text-secondary">Obtained from @BotFather on Telegram</Form.Text>
                </Form.Group>
                <Form.Group className="bic-mb-4">
                  <Form.Label>Telegram Chat / Group ID</Form.Label>
                  <Form.Control
                    type="text"
                    name="telegram_chat_id"
                    placeholder="e.g. -100123456789 or 987654321"
                    value={settings.telegram_chat_id}
                    onChange={handleChange}
                  />
                </Form.Group>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleTestTelegram}
                  disabled={testingTg || settings.telegram_enabled !== 'true' || !settings.telegram_bot_token}
                >
                  <MdSend className="bic-mr-1" />
                  {testingTg ? 'Testing...' : 'Send Test Telegram Alert'}
                </Button>
              </Card.Body>
            </Card>

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
                  disabled={testingSmtp || settings.smtp_enabled !== 'true' || !settings.smtp_host}
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
