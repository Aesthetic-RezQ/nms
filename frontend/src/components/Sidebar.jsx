import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  MdDashboard, MdDevices, MdCategory, MdGroupWork, 
  MdLocationOn, MdWarning, MdBuild, MdAssessment, 
  MdPeople, MdSettings, MdSecurity 
} from 'react-icons/md';
import { useAuth } from '../auth/AuthContext';

export default function Sidebar({ isOpen }) {
  const { isAdmin } = useAuth();

  return (
    <div className={`sidebar ${isOpen ? 'show' : ''}`}>
      <div className="p-4 d-flex align-items-center gap-2 text-white border-bottom border-secondary mb-3">
        <img src="/logo.jpg" alt="NMS Logo" style={{ height: '36px', width: 'auto', objectFit: 'contain' }} />
      </div>
      
      <nav className="nav flex-column px-2">
        <NavLink to="/" className={({isActive}) => `nav-link text-decoration-none ${isActive ? 'active' : ''}`} end>
          <MdDashboard /> Dashboard
        </NavLink>
        <NavLink to="/devices" className={({isActive}) => `nav-link text-decoration-none ${isActive ? 'active' : ''}`}>
          <MdDevices /> Devices
        </NavLink>
        <NavLink to="/incidents" className={({isActive}) => `nav-link text-decoration-none ${isActive ? 'active' : ''}`}>
          <MdWarning /> Incidents
        </NavLink>
        <NavLink to="/maintenance" className={({isActive}) => `nav-link text-decoration-none ${isActive ? 'active' : ''}`}>
          <MdBuild /> Maintenance
        </NavLink>
        <NavLink to="/categories" className={({isActive}) => `nav-link text-decoration-none ${isActive ? 'active' : ''}`}>
          <MdCategory /> Categories
        </NavLink>
        <NavLink to="/groups" className={({isActive}) => `nav-link text-decoration-none ${isActive ? 'active' : ''}`}>
          <MdGroupWork /> Groups
        </NavLink>
        <NavLink to="/locations" className={({isActive}) => `nav-link text-decoration-none ${isActive ? 'active' : ''}`}>
          <MdLocationOn /> Locations
        </NavLink>

        {isAdmin && (
          <>
            <hr className="bg-secondary my-2" />
            <h6 className="px-3 mt-2 mb-1 text-muted text-uppercase" style={{fontSize: '0.75rem'}}>Admin</h6>
            <NavLink to="/users" className={({isActive}) => `nav-link text-decoration-none ${isActive ? 'active' : ''}`}>
              <MdPeople /> Users
            </NavLink>
            <NavLink to="/audit-logs" className={({isActive}) => `nav-link text-decoration-none ${isActive ? 'active' : ''}`}>
              <MdSecurity /> Audit Logs
            </NavLink>
            <NavLink to="/settings" className={({isActive}) => `nav-link text-decoration-none ${isActive ? 'active' : ''}`}>
              <MdSettings /> Settings
            </NavLink>
          </>
        )}
      </nav>
    </div>
  );
}
