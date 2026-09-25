import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom';
import { 
  MdMenu, 
  MdExpandMore, 
  MdDashboard, 
  MdDevices, 
  MdWarning, 
  MdBuild, 
  MdHistory, 
  MdCategory, 
  MdGroupWork, 
  MdLocationOn, 
  MdPeople, 
  MdSecurity, 
  MdSettings 
} from 'react-icons/md';
import Sidebar from './Sidebar';
import { Button } from './bic';
import { useAuth } from '../auth/AuthContext';

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout, isAdmin, isOperator } = useAuth();
  const account = useRef(null);
  const operationsDropdown = useRef(null);
  const adminDropdown = useRef(null);
  const menuButton = useRef(null);
  const location = useLocation();

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
    if (operationsDropdown.current) operationsDropdown.current.open = false;
    if (adminDropdown.current) adminDropdown.current.open = false;
  }, [location.pathname]);

  useEffect(() => {
    const closeDropdowns = event => {
      if (account.current && !account.current.contains(event.target)) account.current.open = false;
      if (operationsDropdown.current && !operationsDropdown.current.contains(event.target)) operationsDropdown.current.open = false;
      if (adminDropdown.current && !adminDropdown.current.contains(event.target)) adminDropdown.current.open = false;
    };
    const onKeyDown = event => {
      if (event.key === 'Escape') {
        if (account.current?.open) { account.current.open = false; account.current.querySelector('summary').focus(); }
        if (operationsDropdown.current?.open) { operationsDropdown.current.open = false; operationsDropdown.current.querySelector('summary').focus(); }
        if (adminDropdown.current?.open) { adminDropdown.current.open = false; adminDropdown.current.querySelector('summary').focus(); }
      }
    };
    document.addEventListener('pointerdown', closeDropdowns);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('pointerdown', closeDropdowns);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, []);

  const closeSidebar = useCallback(() => { setSidebarOpen(false); menuButton.current?.focus(); }, []);

  const isNetworkActive = ['/categories', '/groups', '/locations'].includes(location.pathname);
  const isAdminActive = ['/users', '/audit-logs', '/settings'].includes(location.pathname);

  return (
    <div className="bic-app">
      <a className="bic-btn bic-btn-primary bic-skip-link" href="#main-content">Skip to content</a>
      <Sidebar isOpen={sidebarOpen} onClose={closeSidebar} />
      {sidebarOpen && <button className="bic-sidebar-overlay" aria-label="Close navigation" tabIndex={-1} onClick={closeSidebar} />}
      
      {/* Tabler Horizontal Top Navbar */}
      <header className="bic-navbar">
        <div className="bic-navbar-container">
          <div className="bic-flex bic-items-center bic-gap-3">
            <button 
              ref={menuButton} 
              type="button" 
              className="bic-btn bic-btn-secondary bic-menu-toggle"
              aria-label="Open navigation" 
              aria-controls="app-sidebar" 
              aria-expanded={sidebarOpen}
              onClick={() => setSidebarOpen(true)}
            >
              <MdMenu />
            </button>
            <Link to="/" className="bic-navbar-brand">
              <img src="/logo.jpg" alt="BIC" className="bic-brand-logo" />
              <span className="bic-brand-name">NMS</span>
            </Link>
          </div>

          <nav className="bic-navbar-nav" aria-label="Main horizontal navigation">
            <NavLink to="/" end className={({ isActive }) => 'bic-nav-link' + (isActive ? ' is-active' : '')}>
              <MdDashboard className="bic-icon" /> Dashboard
            </NavLink>
            <NavLink to="/devices" className={({ isActive }) => 'bic-nav-link' + (isActive ? ' is-active' : '')}>
              <MdDevices className="bic-icon" /> Devices
            </NavLink>
            <NavLink to="/incidents" className={({ isActive }) => 'bic-nav-link' + (isActive ? ' is-active' : '')}>
              <MdWarning className="bic-icon" /> Incidents
            </NavLink>
            <NavLink to="/maintenance" className={({ isActive }) => 'bic-nav-link' + (isActive ? ' is-active' : '')}>
              <MdBuild className="bic-icon" /> Maintenance
            </NavLink>
            <NavLink to="/ping-timeouts" className={({ isActive }) => 'bic-nav-link' + (isActive ? ' is-active' : '')}>
              <MdHistory className="bic-icon" /> Ping Timeouts
            </NavLink>

            {isOperator && (
              <details ref={operationsDropdown} className="bic-dropdown">
                <summary className={`bic-nav-link bic-dropdown-toggle${isNetworkActive ? ' is-active' : ''}`}>
                  <MdCategory className="bic-icon" /> Network <MdExpandMore className="bic-account-chevron" />
                </summary>
                <div className="bic-dropdown-menu">
                  <NavLink to="/categories" className={({ isActive }) => 'bic-dropdown-item' + (isActive ? ' is-active' : '')}>
                    <MdCategory className="bic-icon" /> Categories
                  </NavLink>
                  <NavLink to="/groups" className={({ isActive }) => 'bic-dropdown-item' + (isActive ? ' is-active' : '')}>
                    <MdGroupWork className="bic-icon" /> Groups
                  </NavLink>
                  <NavLink to="/locations" className={({ isActive }) => 'bic-dropdown-item' + (isActive ? ' is-active' : '')}>
                    <MdLocationOn className="bic-icon" /> Locations
                  </NavLink>
                </div>
              </details>
            )}

            {isAdmin && (
              <details ref={adminDropdown} className="bic-dropdown">
                <summary className={`bic-nav-link bic-dropdown-toggle${isAdminActive ? ' is-active' : ''}`}>
                  <MdSettings className="bic-icon" /> Administration <MdExpandMore className="bic-account-chevron" />
                </summary>
                <div className="bic-dropdown-menu">
                  <NavLink to="/users" className={({ isActive }) => 'bic-dropdown-item' + (isActive ? ' is-active' : '')}>
                    <MdPeople className="bic-icon" /> Users
                  </NavLink>
                  <NavLink to="/audit-logs" className={({ isActive }) => 'bic-dropdown-item' + (isActive ? ' is-active' : '')}>
                    <MdSecurity className="bic-icon" /> Audit Logs
                  </NavLink>
                  <NavLink to="/settings" className={({ isActive }) => 'bic-dropdown-item' + (isActive ? ' is-active' : '')}>
                    <MdSettings className="bic-icon" /> Settings
                  </NavLink>
                </div>
              </details>
            )}
          </nav>

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
              <hr className="bic-dropdown-divider" />
              <Button variant="secondary" className="bic-w-full" onClick={logout}>Logout</Button>
            </div>
          </details>
        </div>
      </header>

      <main className="bic-main">
        <section id="main-content" className="bic-content" tabIndex={-1}>
          <Outlet />
        </section>
      </main>
    </div>
  );
}
