import React, { useEffect, useState } from 'react';
import { Button, Table, Card, Modal, Form } from '../components/bic';
import { MdAdd, MdEdit, MdDelete } from 'react-icons/md';
import { toast } from '../components/bic/Notifications';
import { get, post, put, del } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import ConfirmDialog from '../components/common/ConfirmDialog';

export default function CategoriesPage() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ id: null, name: '', description: '', icon: '', display_order: 0 });
  const [deleteId, setDeleteId] = useState(null);

  const { isAdmin } = useAuth();

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    setLoading(true);
    try {
      const res = await get('/categories');
      setCategories(res.data);
    } catch (error) {
      toast.error('Failed to load categories');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (category = null) => {
    if (category) {
      setFormData(category);
    } else {
      setFormData({ id: null, name: '', description: '', icon: '', display_order: 0 });
    }
    setShowModal(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      if (formData.id) {
        await put(`/categories/${formData.id}`, formData);
        toast.success('Category updated');
      } else {
        await post('/categories', formData);
        toast.success('Category created');
      }
      setShowModal(false);
      fetchCategories();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save category');
    }
  };

  const handleDelete = async () => {
    try {
      await del(`/categories/${deleteId}`);
      toast.success('Category deleted');
      fetchCategories();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete category');
    } finally {
      setDeleteId(null);
    }
  };

  return (
    <div>
      <div className="bic-page-header">
        <h1 className="bic-page-title">Categories</h1>
        {isAdmin && (
          <Button variant="primary" onClick={() => handleOpenModal()}>
            <MdAdd className="bic-mr-1" /> Add Category
          </Button>
        )}
      </div>

      <Card>
        <Table responsive hover className="bic-mb-0">
          <thead>
            <tr>
              <th>Icon</th>
              <th>Name</th>
              <th>Description</th>
              <th>Order</th>
              <th className="bic-text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="5" className="bic-empty">Loading...</td></tr>
            ) : categories.length === 0 ? (
              <tr><td colSpan="5" className="bic-empty">No categories found</td></tr>
            ) : (
              categories.map(c => (
                <tr key={c.id}>
                  <td>{c.icon}</td>
                  <td>{c.name}</td>
                  <td>{c.description}</td>
                  <td>{c.display_order}</td>
                  <td className="bic-text-right">
                    {isAdmin && (
                      <>
                        <Button variant="secondary" size="sm" className="bic-mr-2" title="Edit category" onClick={() => handleOpenModal(c)}>
                          <MdEdit />
                        </Button>
                        <Button variant="danger" size="sm" title="Delete category" onClick={() => setDeleteId(c.id)}>
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
            <Modal.Title>{formData.id ? 'Edit Category' : 'Add Category'}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Form.Group className="bic-mb-4">
              <Form.Label>Name *</Form.Label>
              <Form.Control required value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
            </Form.Group>
            <Form.Group className="bic-mb-4">
              <Form.Label>Description</Form.Label>
              <Form.Control as="textarea" value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} />
            </Form.Group>
            <Form.Group className="bic-mb-4">
              <Form.Label>Icon (Text/Emoji)</Form.Label>
              <Form.Control value={formData.icon} onChange={e => setFormData({...formData, icon: e.target.value})} />
            </Form.Group>
            <Form.Group className="bic-mb-4">
              <Form.Label>Display Order</Form.Label>
              <Form.Control type="number" value={formData.display_order} onChange={e => setFormData({...formData, display_order: parseInt(e.target.value) || 0})} />
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
        title="Delete Category"
        message="Are you sure you want to delete this category?"
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />
    </div>
  );
}
