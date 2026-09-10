import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { get, post } from '../api/client';
import { Spinner } from '../components/bic';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const identityRequest = useRef(0);

  const loadUser = async ({ clearOnError = true } = {}) => {
    const requestId = ++identityRequest.current;
    try {
      const res = await get('/auth/me');
      if (requestId === identityRequest.current) setUser(res.data);
      return res.data;
    } catch (error) {
      if (clearOnError && requestId === identityRequest.current) setUser(null);
      return null;
    }
  };

  useEffect(() => {
    loadUser().finally(() => setLoading(false));
    const refreshIdentity = () => { loadUser({ clearOnError: false }); };
    window.addEventListener('focus', refreshIdentity);
    const interval = window.setInterval(refreshIdentity, 30000);
    return () => {
      window.removeEventListener('focus', refreshIdentity);
      window.clearInterval(interval);
    };
  }, []);

  const login = async (username, password) => {
    // Invalidate the initial anonymous /auth/me request so it cannot race and
    // clear the freshly authenticated CentralAuth identity.
    identityRequest.current += 1;
    const res = await post('/auth/login', { username, password });
    setUser(res.data.user || await loadUser({ clearOnError: true }));
  };

  const logout = async () => {
    identityRequest.current += 1;
    try { await post('/auth/logout'); } finally { setUser(null); }
  };

  const refreshToken = async () => {
    const res = await post('/auth/refresh');
    setUser(res.data.user || await loadUser());
  };

  const isAdmin = user?.role === 'NMS_ADMIN' || user?.role === 'admin';
  const isOperator = isAdmin || user?.role === 'NMS_OPERATOR' || user?.role === 'operator';

  const value = { user, token: null, loading, login, logout, refreshToken, isAdmin, isOperator, isViewer: !!user };

  return <AuthContext.Provider value={value}>
    {loading ? <div className="bic-auth"><Spinner label="Verifying session" /></div> : children}
  </AuthContext.Provider>;
};

export const useAuth = () => useContext(AuthContext);
