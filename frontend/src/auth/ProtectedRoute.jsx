import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { Spinner } from '../components/bic';

export default function ProtectedRoute({ children, requireAdmin }) {
  const { user, loading, isAdmin } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="bic-flex bic-justify-center bic-items-center bic-auth">
        <Spinner />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requireAdmin && !isAdmin) {
    return (
      <div>
        <div className="bic-page-header"><h1 className="bic-page-title">Access restricted</h1></div>
        <div className="bic-alert bic-alert-danger" role="alert">403 - Forbidden: Admin access required.</div>
      </div>
    );
  }

  return children;
}
