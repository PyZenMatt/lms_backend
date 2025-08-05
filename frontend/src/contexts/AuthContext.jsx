
import React, { createContext, useContext, useState, useEffect } from 'react';
import { fetchUserProfile } from '../services/api/dashboard';
import { login as apiLogin, logout as apiLogout } from '../services/api/auth';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Clear wallet state from localStorage to prevent cross-user contamination
  useEffect(() => {
    localStorage.removeItem('isWalletLocked');
    localStorage.removeItem('lockedWalletAddress');
    localStorage.removeItem('connectedWalletAddress');
    console.log('🧹 Wallet localStorage cleared for per-user isolation');
  }, []);

  const refreshUser = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetchUserProfile();
      setUser(response.data);
      setIsAuthenticated(true);
    } catch (err) {
      console.error('Error fetching user profile:', err);
      setError('Errore nel caricamento del profilo utente');
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  // Login persistente
  const login = async (credentials) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiLogin(credentials);
      const token = response.data.access || response.data.token;
      localStorage.setItem('accessToken', token);
      await refreshUser();
      setIsAuthenticated(true);
      return true;
    } catch (err) {
      setError('Login fallito');
      setUser(null);
      setIsAuthenticated(false);
      return false;
    } finally {
      setLoading(false);
    }
  };

  // Logout robusto
  const logout = async () => {
    setLoading(true);
    try {
      await apiLogout();
    } catch {}
    localStorage.removeItem('accessToken');
    setUser(null);
    setIsAuthenticated(false);
    setLoading(false);
  };

  useEffect(() => {
    // Persist login su mount
    const token = localStorage.getItem('accessToken') || 
                  localStorage.getItem('token') || 
                  localStorage.getItem('access');
    if (token) {
      setIsAuthenticated(true);
      refreshUser();
    } else {
      setIsAuthenticated(false);
      setLoading(false);
    }
  }, []);

  const value = {
    user,
    loading,
    error,
    isAuthenticated,
    login,
    logout,
    refreshUser,
    setUser
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
