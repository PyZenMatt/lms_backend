// Utility per collegare il logout React anche ai menu statici
import { useAuth } from '../contexts/AuthContext';

export function getLogoutAction() {
  // Hook non usabile direttamente fuori da React, quindi workaround:
  return async function logoutAction() {
    // Prova a trovare il logout React in window (iniettato da App)
    if (window.__reactLogout) {
      await window.__reactLogout();
    } else {
      // Fallback legacy
      localStorage.removeItem('accessToken');
      localStorage.removeItem('token');
      window.location.href = '/auth/signin-1';
    }
  };
}
