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
      setError('Sessione scaduta o token non valido. Effettua di nuovo il login.');
      setUser(null);
      setIsAuthenticated(false);
      // Logout automatico se il token non è valido
      localStorage.removeItem('accessToken');
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

  // Logout robusto - cleanup completo localStorage
  const logout = async () => {
    console.log('🔓 Starting complete logout process...');
    setLoading(true);

    try {
      const refreshToken = localStorage.getItem('refreshToken') || localStorage.getItem('refresh');
      await apiLogout(refreshToken);
      console.log('🔓 API logout completed');
    } catch (error) {
      console.error('🔓 API logout error:', error);
    }

    // Cleanup completo del localStorage - elimina TUTTI i possibili token
    const tokensToRemove = [
      'access', // Il token che hai trovato nel localStorage
      'accessToken',
      'refreshToken',
      'refresh',
      'token',
      'jwt',
      'authToken',
      'userToken'
    ];

    tokensToRemove.forEach((tokenKey) => {
      if (localStorage.getItem(tokenKey)) {
        console.log(`🔓 Removing ${tokenKey} from localStorage`);
        localStorage.removeItem(tokenKey);
      }
    });

    // Reset stato React
    setUser(null);
    setIsAuthenticated(false);
    setLoading(false);

    console.log('🔓 Complete logout finished - localStorage cleaned');
    // Non facciamo redirect qui - lasciamo che lo gestisca il chiamante
  };

  useEffect(() => {
    // Espone la funzione di logout su window per i menu statici
    if (typeof window !== 'undefined') {
      window.__reactLogout = logout;
    }
    // Persist login su mount
    const token = localStorage.getItem('accessToken') || localStorage.getItem('token') || localStorage.getItem('access');
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

  // Blocca rendering figli finché loading è true
  return (
    <AuthContext.Provider value={value}>
      {loading ? (
        <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="text-center">
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Caricamento...</span>
            </div>
            <div className="mt-2 text-muted">Verifica autenticazione...</div>
            {error && <div className="border rounded-md p-3 bg-muted text-muted-foreground bg-warning/15 border-warning text-warning-foreground mt-3">{error}</div>}
          </div>
        </div>
      ) : (
        children
      )}
    </AuthContext.Provider>
  );
};

export default AuthContext;
