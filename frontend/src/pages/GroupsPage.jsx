import React, { useEffect, useState } from 'react';
import { Button, Table, Card, Modal, Form } from '../components/bic';
import { MdAdd, MdEdit, MdDelete } from 'react-icons/md';
import { toast } from '../components/bic/Notifications';
import { get, post, put, del } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import ConfirmDialog from '../components/common/ConfirmDialog';

export default function GroupsPage() {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ id: null, name: '', description: '' });
  const [deleteId, setDeleteId] = useState(null);

  const { isAdmin } = useAuth();

  useEffect(() => {
    fetchGroups();
  }, []);

  const fetchGroups = async () => {
    setLoading(true);
    try {
      const res = await get('/groups');
      setGroups(res.data);
    } catch (error) {
      toast.error('Failed to load groups');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (group = null) => {
    if (group) {
      setFormData(group);
    } else {
      setFormData({ id: null, name: '', description: '' });
    }
    setShowModal(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      if (formData.id) {
        await put(`/groups/${formData.id}`, formData);
        toast.success('Group updated');
      } else {
        await post('/groups', formData);
        toast.success('Group created');
      }
      setShowModal(false);
      fetchGroups();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save group');
    }
  };

  const handleDelete = async () => {
    try {
      await del(`/groups/${deleteId}`);
      toast.success('Group deleted');
      fetchGroups();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete group');
    } finally {
      setDeleteId(null);
    }
  };

  return (
    <div>
      <div className="bic-page-header">
        <h1 className="bic-page-title">Groups</h1>
        {isAdmin && (
          <Button variant="primary" onClick={() => handleOpenModal()}>
            <MdAdd className="bic-mr-1" /> Add Group
          </Button>
        )}
      </div>

      <Card>
        <Table responsive hover className="bic-mb-0">
          <thead>
            <tr>
              <th>Name</th>
              <th>Description</th>
              <th className="bic-text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="3" className="bic-empty">Loading...</td></tr>
            ) : groups.length === 0 ? (
              <tr><td colSpan="3" className="bic-empty">No groups found</td></tr>
            ) : (
              groups.map(g => (
                <tr key={g.id}>
                  <td>{g.name}</td>
                  <td>{g.description}</td>
                  <td className="bic-text-right">
                    {isAdmin && (
                      <>
                        <Button variant="secondary" size="sm" className="bic-mr-2" title="Edit group" onClick={() => handleOpenModal(g)}>
                          <MdEdit />
                        </Button>
                        <Button variant="danger" size="sm" title="Delete group" onClick={() => setDeleteId(g.id)}>
                          <MdDelete />
                        </Button>
                      </>
                    )}
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
            <Modal.Title>{formData.id ? 'Edit Group' : 'Add Group'}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Form.Group className="bic-mb-4">
              <Form.Label>Name *</Form.Label>
              <Form.Control required value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
            </Form.Group>
            <Form.Group className="bic-mb-4">
              <Form.Label>Description</Form.Label>
              <Form.Control as="textarea" value={formData.description || ''} onChange={e => setFormData({...formData, description: e.target.value})} />
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
        title="Delete Group"
        message="Are you sure you want to delete this group?"
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />
    </div>
  );
}
