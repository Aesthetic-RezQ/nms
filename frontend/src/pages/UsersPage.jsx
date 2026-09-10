import React, { useEffect, useState } from 'react';
import { Alert, Badge, Card, Spinner, Table } from '../components/bic';
import { toast } from '../components/bic/Notifications';
import { get } from '../api/client';

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const fetchUsers = async () => {
      setLoading(true);
      try {
        const res = await get('/users?page_size=100');
        if (active) setUsers(res.data.data || res.data.items || (Array.isArray(res.data) ? res.data : []));
      } catch (error) {
        if (active) toast.error('Failed to load cached identities');
      } finally {
        if (active) setLoading(false);
      }
    };
    fetchUsers();
    return () => { active = false; };
  }, []);

  return (
    <div>
      <div className="bic-page-header">
        <div>
          <p className="bic-page-kicker">ADMINISTRATION</p>
          <h1 className="bic-page-title">Users</h1>
          <p className="bic-page-subtitle">CentralAuth identities currently known to NMS.</p>
        </div>
      </div>

      <Alert variant="info" className="bic-mb-6">
        Create users, change roles, and disable access in CentralAuth. NMS keeps this read-only cache for audit and operational references.
      </Alert>

      <Card>
        <Card.Header>
          <h2 className="bic-section-title bic-mb-0">Identity directory</h2>
          <span className="bic-text-secondary bic-text-sm">{users.length} cached identities</span>
        </Card.Header>
        <Table responsive hover className="bic-mb-0">
          <thead>
            <tr>
              <th>Username</th>
              <th>Email</th>
              <th>Full Name</th>
              <th>Role</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="5" className="bic-empty"><Spinner size="sm" /> Loading identities...</td></tr>
            ) : users.length === 0 ? (
              <tr><td colSpan="5" className="bic-empty">No identities have signed in to NMS yet.</td></tr>
            ) : users.map(user => (
              <tr key={user.id}>
                <td className="bic-font-semibold">{user.username}</td>
                <td>{user.email}</td>
                <td>{user.full_name || '—'}</td>
                <td><Badge bg="info">{user.role}</Badge></td>
                <td>{user.is_active ? <Badge bg="success">Active</Badge> : <Badge bg="info">Inactive</Badge>}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Card>
    </div>
  );
}
