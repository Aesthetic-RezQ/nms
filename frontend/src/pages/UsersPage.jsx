import React, { useEffect, useState } from 'react';
import { Button, Table, Card, Modal, Form, Badge } from 'react-bootstrap';
import { MdAdd, MdEdit, MdDelete } from 'react-icons/md';
import { toast } from 'react-toastify';
import { get, post, put, del } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import ConfirmDialog from '../components/common/ConfirmDialog';
import { USER_ROLES } from '../utils/constants';

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user: currentUser } = useAuth();
  
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ id: null, username: '', email: '', password: '', full_name: '', role: 'viewer', is_active: true });
  const [deleteId, setDeleteId] = useState(null);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await get('/users?page_size=100');
      setUsers(res.data.data || res.data.items || (Array.isArray(res.data) ? res.data : []));
    } catch (error) {
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (usr = null) => {
    if (usr) {
      setFormData({ ...usr, password: '' });
    } else {
      setFormData({ id: null, username: '', email: '', password: '', full_name: '', role: 'viewer', is_active: true });
    }
    setShowModal(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      if (formData.id) {
        const payload = { ...formData };
        delete payload.password; // Admin edits shouldn't blindly update password unless intended
        await put(`/users/${formData.id}`, payload);
        toast.success('User updated');
      } else {
        await post('/users', formData);
        toast.success('User created');
      }
      setShowModal(false);
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save user');
    }
  };

  const handleDelete = async () => {
    if (deleteId === currentUser.id) {
      toast.error("Cannot delete yourself!");
      setDeleteId(null);
      return;
    }
    try {
      await del(`/users/${deleteId}`);
      toast.success('User deleted');
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete user');
    } finally {
      setDeleteId(null);
    }
  };

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Users</h2>
        <Button variant="primary" onClick={() => handleOpenModal()}>
          <MdAdd className="me-1" /> Add User
        </Button>
      </div>

      <Card className="shadow-sm">
        <Table responsive hover className="mb-0">
          <thead className="table-light">
            <tr>
              <th>Username</th>
              <th>Email</th>
              <th>Full Name</th>
              <th>Role</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="6" className="text-center py-4">Loading...</td></tr>
            ) : users.length === 0 ? (
              <tr><td colSpan="6" className="text-center py-4">No users found</td></tr>
            ) : (
              users.map(u => (
                <tr key={u.id}>
                  <td>{u.username}</td>
                  <td>{u.email}</td>
                  <td>{u.full_name}</td>
                  <td><Badge bg="secondary">{u.role}</Badge></td>
                  <td>
                    {u.is_active ? <Badge bg="success">Active</Badge> : <Badge bg="danger">Inactive</Badge>}
                  </td>
                  <td>
                    <Button variant="link" className="p-0 text-primary me-2" onClick={() => handleOpenModal(u)}>
                      <MdEdit size={18} />
                    </Button>
                    <Button 
                      variant="link" 
                      className={`p-0 ${u.id === currentUser.id ? 'text-muted' : 'text-danger'}`} 
                      disabled={u.id === currentUser.id}
                      onClick={() => setDeleteId(u.id)}
                    >
                      <MdDelete size={18} />
                    </Button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </Table>
      </Card>

      <Modal show={showModal} onHide={() => setShowModal(false)}>
        <Form onSubmit={handleSave}>
          <Modal.Header closeButton>
            <Modal.Title>{formData.id ? 'Edit User' : 'Add User'}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Username *</Form.Label>
              <Form.Control required value={formData.username} onChange={e => setFormData({...formData, username: e.target.value})} disabled={!!formData.id} />
            </Form.Group>
            {!formData.id && (
              <Form.Group className="mb-3">
                <Form.Label>Password *</Form.Label>
                <Form.Control required type="password" value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})} />
              </Form.Group>
            )}
            <Form.Group className="mb-3">
              <Form.Label>Email *</Form.Label>
              <Form.Control required type="email" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Full Name</Form.Label>
              <Form.Control value={formData.full_name} onChange={e => setFormData({...formData, full_name: e.target.value})} />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Role</Form.Label>
              <Form.Select value={formData.role} onChange={e => setFormData({...formData, role: e.target.value})}>
                {USER_ROLES.map(r => <option key={r} value={r}>{r}</option>)}
              </Form.Select>
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Check type="checkbox" label="Active" checked={formData.is_active} onChange={e => setFormData({...formData, is_active: e.target.checked})} />
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowModal(false)}>Cancel</Button>
            <Button variant="primary" type="submit">Save</Button>
          </Modal.Footer>
        </Form>
      </Modal>

      <ConfirmDialog
        show={!!deleteId}
        title="Delete User"
        message="Are you sure you want to delete this user? This cannot be undone."
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />
    </div>
  );
}
