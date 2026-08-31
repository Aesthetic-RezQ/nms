import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Form, Button, Alert, Container, Spinner } from 'react-bootstrap';

import { useAuth } from './AuthContext';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to login. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <Container className="d-flex justify-content-center">
        <Card className="login-card p-4">
          <div className="text-center mb-4">
            <img src="/logo.jpg" alt="NMS Logo" style={{ height: '64px', width: 'auto', objectFit: 'contain' }} />
            <h3 className="mt-3 text-dark">NMS Login</h3>
            <p className="text-muted">Network Monitoring System</p>
          </div>
          {error && <Alert variant="danger">{error}</Alert>}
          <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-3" controlId="username">
              <Form.Label>Username</Form.Label>
              <Form.Control 
                type="text" 
                placeholder="Enter username" 
                value={username} 
                onChange={(e) => setUsername(e.target.value)} 
                required 
              />
            </Form.Group>
            <Form.Group className="mb-4" controlId="password">
              <Form.Label>Password</Form.Label>
              <Form.Control 
                type="password" 
                placeholder="Password" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                required 
              />
            </Form.Group>
            <Button variant="primary" type="submit" className="w-100 py-2" disabled={loading}>
              {loading ? <Spinner animation="border" size="sm" /> : 'Login'}
            </Button>
          </Form>
        </Card>
      </Container>
    </div>
  );
}
