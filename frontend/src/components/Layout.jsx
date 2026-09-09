import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { MdMenu, MdPerson, MdExpandMore } from 'react-icons/md';
import Sidebar from './Sidebar';
import { Button } from './bic';
import { useAuth } from '../auth/AuthContext';

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuth();
  const account = useRef(null);
  const menuButton = useRef(null);
  const location = useLocation();

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
            <strong className="bic-topbar-label">Network Monitoring System</strong>
          </div>
          <details ref={account} className="bic-dropdown">
            <summary className="bic-btn bic-btn-secondary"><MdPerson /> {user?.full_name || user?.username || 'User'} <MdExpandMore /></summary>
            <div className="bic-dropdown-menu">
              <p className="bic-text-secondary bic-text-sm">Role: {user?.role}</p>
              <Button variant="secondary" className="bic-w-full" onClick={logout}>Logout</Button>
            </div>
          </details>
        </header>
        <section id="main-content" className="bic-content" tabIndex={-1}><Outlet /></section>
      </main>
    </div>
  );
}
