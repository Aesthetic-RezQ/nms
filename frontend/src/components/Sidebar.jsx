import React, { useEffect, useRef } from 'react';
import { NavLink } from 'react-router-dom';
import { MdDashboard, MdDevices, MdCategory, MdGroupWork, MdLocationOn, MdWarning, MdBuild, MdPeople, MdSettings, MdSecurity } from 'react-icons/md';
import { useAuth } from '../auth/AuthContext';
import { Button } from './bic';

const operations = [
  ['/devices', 'Devices', MdDevices], ['/incidents', 'Incidents', MdWarning],
  ['/maintenance', 'Maintenance', MdBuild], ['/categories', 'Categories', MdCategory],
  ['/groups', 'Groups', MdGroupWork], ['/locations', 'Locations', MdLocationOn],
];
const administration = [['/users', 'Users', MdPeople], ['/audit-logs', 'Audit Logs', MdSecurity], ['/settings', 'Settings', MdSettings]];

export default function Sidebar({ isOpen, onClose }) {
  const { isAdmin } = useAuth();
  const sidebar = useRef(null);
  useEffect(() => {
    if (!isOpen) return;
    const panel = sidebar.current;
    // Wait for the responsive visibility change before moving keyboard focus.
    const focusFrame = requestAnimationFrame(() => panel.querySelector('button').focus());
    const keydown = event => {
      if (event.key === 'Escape') { event.preventDefault(); onClose(); }
      if (event.key === 'Tab') {
        const items = [...panel.querySelectorAll('button, a')];
        const first = items[0], last = items.at(-1);
        if (!panel.contains(document.activeElement)) { event.preventDefault(); first.focus(); }
        else if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }
    };
    const media = window.matchMedia('(min-width: 769px)');
    const resize = () => { if (media.matches) onClose(); };
    document.addEventListener('keydown', keydown);
    media.addEventListener('change', resize);
    return () => { cancelAnimationFrame(focusFrame); document.removeEventListener('keydown', keydown); media.removeEventListener('change', resize); };
  }, [isOpen, onClose]);

  const link = ([to, label, Icon]) => <NavLink key={to} to={to} end={to === '/'}
    onClick={isOpen ? onClose : undefined} className={({ isActive }) => 'bic-nav-link' + (isActive ? ' is-active' : '')}>
    <Icon /> {label}
  </NavLink>;

  return <aside ref={sidebar} id="app-sidebar" className={'bic-sidebar' + (isOpen ? ' is-open' : '')} aria-label="Application navigation">
    <div className="bic-brand"><img src="/logo.jpg" alt="BIC" className="bic-brand-logo" /></div>
    <div className="bic-sidebar-heading"><strong>Navigation</strong><Button variant="secondary" size="sm" onClick={onClose}>Close</Button></div>
    <nav className="bic-nav" aria-label="Main navigation">
      <div className="bic-nav-section">Overview</div>
      {link(['/', 'Dashboard', MdDashboard])}
      <div className="bic-nav-section">Operations</div>
      {operations.map(link)}
      {isAdmin && <><div className="bic-nav-section">Administration</div>{administration.map(link)}</>}
    </nav>
  </aside>;
}
