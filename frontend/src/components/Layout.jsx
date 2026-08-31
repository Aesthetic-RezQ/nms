import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Dropdown } from 'react-bootstrap';
import { MdMenu, MdPerson } from 'react-icons/md';
import Sidebar from './Sidebar';
import { useAuth } from '../auth/AuthContext';

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuth();

  return (
    <div className="d-flex">
      <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />
      
      <div className="main-content flex-grow-1">
        <div className="topbar">
          <button 
            className="btn btn-light d-md-none"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            <MdMenu size={24} />
          </button>
          
          <div className="ms-auto">
            <Dropdown align="end">
              <Dropdown.Toggle variant="light" id="dropdown-basic" className="d-flex align-items-center gap-2">
                <MdPerson /> {user?.full_name || user?.username || 'User'}
              </Dropdown.Toggle>

              <Dropdown.Menu>
                <Dropdown.Item disabled>Role: {user?.role}</Dropdown.Item>
                <Dropdown.Divider />
                <Dropdown.Item onClick={logout}>Logout</Dropdown.Item>
              </Dropdown.Menu>
            </Dropdown>
          </div>
        </div>

        <div className="content-wrapper">
          <Outlet />
        </div>
      </div>
      
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div 
          className="position-fixed top-0 start-0 w-100 h-100 bg-dark opacity-50 d-md-none" 
          style={{ zIndex: 999 }}
          onClick={() => setSidebarOpen(false)}
        ></div>
      )}
    </div>
  );
}
