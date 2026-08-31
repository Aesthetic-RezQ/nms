import React, { useEffect, useState } from 'react';
import { Button, Table, Card, Modal, Form } from 'react-bootstrap';
import { MdAdd, MdEdit, MdDelete } from 'react-icons/md';
import { toast } from 'react-toastify';
import { get, post, put, del } from '../api/client';
import ConfirmDialog from '../components/common/ConfirmDialog';

export default function LocationsPage() {
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ id: null, name: '', description: '', address: '' });
  const [deleteId, setDeleteId] = useState(null);

  useEffect(() => {
    fetchLocations();
  }, []);

  const fetchLocations = async () => {
    setLoading(true);
    try {
      const res = await get('/locations');
      setLocations(res.data);
    } catch (error) {
      toast.error('Failed to load locations');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (loc = null) => {
    if (loc) {
      setFormData(loc);
    } else {
      setFormData({ id: null, name: '', description: '', address: '' });
    }
    setShowModal(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      if (formData.id) {
        await put(`/locations/${formData.id}`, formData);
        toast.success('Location updated');
      } else {
        await post('/locations', formData);
        toast.success('Location created');
      }
      setShowModal(false);
      fetchLocations();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save location');
    }
  };

  const handleDelete = async () => {
    try {
      await del(`/locations/${deleteId}`);
      toast.success('Location deleted');
      fetchLocations();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete location');
    } finally {
      setDeleteId(null);
    }
  };

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Locations</h2>
        <Button variant="primary" onClick={() => handleOpenModal()}>
          <MdAdd className="me-1" /> Add Location
        </Button>
      </div>

      <Card className="shadow-sm">
        <Table responsive hover className="mb-0">
          <thead className="table-light">
            <tr>
              <th>Name</th>
              <th>Description</th>
              <th>Address</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="4" className="text-center py-4">Loading...</td></tr>
            ) : locations.length === 0 ? (
              <tr><td colSpan="4" className="text-center py-4">No locations found</td></tr>
            ) : (
              locations.map(l => (
                <tr key={l.id}>
                  <td>{l.name}</td>
                  <td>{l.description}</td>
                  <td>{l.address}</td>
                  <td>
                    <Button variant="link" className="p-0 text-primary me-2" onClick={() => handleOpenModal(l)}>
                      <MdEdit size={18} />
                    </Button>
                    <Button variant="link" className="p-0 text-danger" onClick={() => setDeleteId(l.id)}>
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
            <Modal.Title>{formData.id ? 'Edit Location' : 'Add Location'}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Name *</Form.Label>
              <Form.Control required value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Description</Form.Label>
              <Form.Control as="textarea" value={formData.description || ''} onChange={e => setFormData({...formData, description: e.target.value})} />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Address</Form.Label>
              <Form.Control value={formData.address || ''} onChange={e => setFormData({...formData, address: e.target.value})} />
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
        title="Delete Location"
        message="Are you sure you want to delete this location?"
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />
    </div>
  );
}
