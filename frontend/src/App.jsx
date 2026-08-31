import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import { AuthProvider } from './auth/AuthContext';
import ProtectedRoute from './auth/ProtectedRoute';
import Layout from './components/Layout';
import LoginPage from './auth/LoginPage';
import DashboardPage from './pages/DashboardPage';
import DevicesPage from './pages/DevicesPage';
import DeviceDetailPage from './pages/DeviceDetailPage';
import DeviceFormPage from './pages/DeviceFormPage';
import IncidentsPage from './pages/IncidentsPage';
import MaintenancePage from './pages/MaintenancePage';
import CategoriesPage from './pages/CategoriesPage';
import GroupsPage from './pages/GroupsPage';
import LocationsPage from './pages/LocationsPage';
import UsersPage from './pages/UsersPage';
import AuditLogsPage from './pages/AuditLogsPage';
import SettingsPage from './pages/SettingsPage';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<DashboardPage />} />
            <Route path="devices" element={<DevicesPage />} />
            <Route path="devices/new" element={<DeviceFormPage />} />
            <Route path="devices/:id" element={<DeviceDetailPage />} />
            <Route path="devices/:id/edit" element={<DeviceFormPage />} />
            <Route path="incidents" element={<IncidentsPage />} />
            <Route path="maintenance" element={<MaintenancePage />} />
            <Route path="categories" element={<CategoriesPage />} />
            <Route path="groups" element={<GroupsPage />} />
            <Route path="locations" element={<LocationsPage />} />
            
            {/* Admin only routes */}
            <Route path="users" element={<ProtectedRoute requireAdmin><UsersPage /></ProtectedRoute>} />
            <Route path="audit-logs" element={<ProtectedRoute requireAdmin><AuditLogsPage /></ProtectedRoute>} />
            <Route path="settings" element={<ProtectedRoute requireAdmin><SettingsPage /></ProtectedRoute>} />
            
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <ToastContainer position="top-right" autoClose={3000} />
    </AuthProvider>
  );
}

export default App;
