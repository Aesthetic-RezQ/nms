import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { MdMenu, MdExpandMore } from 'react-icons/md';
import Sidebar from './Sidebar';
import { Button } from './bic';
import { useAuth } from '../auth/AuthContext';

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuth();
  const account = useRef(null);
  const menuButton = useRef(null);
  const location = useLocation();
  const pageName = location.pathname.split('/').filter(Boolean)[0] || 'dashboard';
  const pageLabel = pageName.replace(/-/g, ' ').replace(/\b\w/g, letter => letter.toUpperCase());

  const displayName = user?.full_name || user?.username || 'User';
  const initial = displayName.charAt(0).toUpperCase();
  const getRoleLabel = (role) => {
    if (!role) return 'User';
    const upper = String(role).toUpperCase();
    if (upper === 'ADMIN') return 'Administrator';
    if (upper === 'OPERATOR') return 'Operator';
    if (upper === 'VIEWER') return 'Viewer';
    return role.charAt(0).toUpperCase() + role.slice(1).toLowerCase();
  };
  const userRole = getRoleLabel(user?.role);

  useEffect(() => {
    setSidebarOpen(false);
    if (account.current) account.current.open = false;
  }, [location.pathname]);

  useEffect(() => {
    const closeAccount = event => {
      if (account.current && !account.current.contains(event.target)) account.current.open = false;
    };
    const onKeyDown = event => {
      if (event.key === 'Escape' && account.current?.open) {
        account.current.open = false;
        account.current.querySelector('summary').focus();
      }
    };
    document.addEventListener('pointerdown', closeAccount);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('pointerdown', closeAccount);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, []);

  const closeSidebar = useCallback(() => { setSidebarOpen(false); menuButton.current?.focus(); }, []);

  return (
    <div className="bic-app">
      <a className="bic-btn bic-btn-primary bic-skip-link" href="#main-content">Skip to content</a>
      <Sidebar isOpen={sidebarOpen} onClose={closeSidebar} />
      {sidebarOpen && <button className="bic-sidebar-overlay" aria-label="Close navigation" tabIndex={-1} onClick={closeSidebar} />}
      <main className="bic-main">
        <header className="bic-topbar">
          <div className="bic-flex bic-items-center bic-gap-3">
            <button ref={menuButton} type="button" className="bic-btn bic-btn-secondary bic-menu-toggle"
              aria-label="Open navigation" aria-controls="app-sidebar" aria-expanded={sidebarOpen}
              onClick={() => setSidebarOpen(true)}><MdMenu /></button>
            <div className="bic-topbar-heading">
              <span className="bic-topbar-eyebrow">NMS Workspace</span>
              <strong className="bic-topbar-label">{pageLabel}</strong>
            </div>
          </div>
          <details ref={account} className="bic-dropdown">
            <summary className="bic-account-btn">
              <span className="bic-account-avatar" aria-hidden="true">{initial}</span>
              <span className="bic-account-details">
                <span className="bic-account-name">{displayName}</span>
                <span className="bic-account-role">{userRole}</span>
              </span>
              <MdExpandMore className="bic-account-chevron" />
            </summary>
            <div className="bic-dropdown-menu">
              <p className="bic-dropdown-name">{displayName}</p>
              <p className="bic-text-secondary bic-text-sm">{user?.email}</p>
              <p className="bic-text-secondary bic-text-sm">Role: {userRole}</p>
              <Button variant="secondary" className="bic-w-full" onClick={logout}>Logout</Button>
            </div>
          </details>
        </header>
        <section id="main-content" className="bic-content" tabIndex={-1}><Outlet /></section>
      </main>
    </div>
  );
}
