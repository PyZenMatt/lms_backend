import React from 'react';
import { createRoot } from 'react-dom/client';

import { ConfigProvider } from './contexts/ConfigContext';
import { AuthProvider } from './contexts/AuthContext';
import { Web3Provider } from './contexts/Web3Context';
import { NotificationProvider } from './contexts/NotificationContext';

import './index.scss';
import App from './App';
import reportWebVitals from './reportWebVitals';

const container = document.getElementById('root');
const root = createRoot(container);
root.render(
  <ConfigProvider>
    <AuthProvider>
      <Web3Provider>
        <NotificationProvider>
          <App />
        </NotificationProvider>
      </Web3Provider>
    </AuthProvider>
  </ConfigProvider>
);

reportWebVitals();
