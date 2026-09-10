import React, { createContext, useContext, useEffect, useState } from 'react';
import { get, post } from '../api/client';
import { Spinner } from '../components/bic';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadUser = async () => {
    try {
      const res = await get('/auth/me');
      setUser(res.data);
      return res.data;
    } catch (error) {
      setUser(null);
      return null;
    }
  };

  useEffect(() => {
    loadUser().finally(() => setLoading(false));
  }, []);

  const login = async (username, password) => {
    const res = await post('/auth/login', { username, password });
    setUser(res.data.user || await loadUser());
  };

  const logout = async () => {
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
