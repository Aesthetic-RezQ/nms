import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Form, Button, Alert, Spinner } from '../components/bic';

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
    <main className="bic-auth">
        <Card className="bic-auth-card">
          <Card.Body>
          <div className="bic-text-center bic-mb-6">
            <img src="/logo.jpg" alt="BIC" className="bic-auth-logo" />
            <h1 className="bic-page-title">NMS Login</h1>
            <p className="bic-page-subtitle">Network Monitoring System</p>
          </div>
          {error && <Alert variant="danger">{error}</Alert>}
          <Form onSubmit={handleSubmit}>
            <Form.Group controlId="username">
              <Form.Label>Username</Form.Label>
              <Form.Control 
                type="text" 
                autoComplete="username"
                placeholder="Enter username" 
                value={username} 
                onChange={(e) => setUsername(e.target.value)} 
                required 
              />
            </Form.Group>
            <Form.Group controlId="password">
              <Form.Label>Password</Form.Label>
              <Form.Control 
                type="password" 
                autoComplete="current-password"
                placeholder="Password" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                required 
              />
            </Form.Group>
            <Button variant="primary" type="submit" className="bic-w-full" disabled={loading}>
              {loading ? <><Spinner size="sm" /> Signing in...</> : 'Login'}
            </Button>
          </Form>
          </Card.Body>
        </Card>
    </main>
  );
}
