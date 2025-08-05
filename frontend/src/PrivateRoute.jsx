import React from 'react';
import { Navigate } from 'react-router-dom';

const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem('token'); // Recupera il token dal localStorage
  return token ? children : <Navigate to="/auth/signin-1" />;
};

export default PrivateRoute;