import api from '../core/axiosClient';

export const fetchUserProfile = async () => {
  return api.get('profile/'); // <-- modifica l'endpoint secondo la tua API
};

// Per lo studente: corsi acquistati e saldo
export const fetchStudentDashboard = async () => {
  return api.get('dashboard/student/');
};

// Per il docente: corsi creati e guadagni
export const fetchTeacherDashboard = async () => {
  return api.get('dashboard/teacher/');
};

// Sottomissioni esercizi dello studente (endpoint corretto)
export const fetchStudentSubmissions = async () => {
  return api.get('exercises/submissions/'); // endpoint corretto secondo urls.py
};

export const updateUserProfile = async (data) => {
  // Se data è FormData, rimuovi il Content-Type header per permettere al browser di impostarlo correttamente
  const config = {};
  if (data instanceof FormData) {
    // Non impostare Content-Type per FormData - il browser lo fa automaticamente con il boundary
    config.transformRequest = [(data) => data];
  }
  return api.put('profile/', data, config);
};

// Wallet management
export const connectWallet = async (walletAddress) => {
  return api.post('wallet/connect/', { wallet_address: walletAddress });
};

export const disconnectWallet = async () => {
  return api.post('wallet/disconnect/');
};
