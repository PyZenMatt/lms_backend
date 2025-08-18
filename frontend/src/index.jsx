import React from 'react';
import { createRoot } from 'react-dom/client';

import { ConfigProvider } from './contexts/ConfigContext';
import { AuthProvider } from './contexts/AuthContext';
import { Web3Provider } from './contexts/Web3Context';
import { NotificationProvider } from './contexts/NotificationContext';

import './styles/tokens.css';
// import './index.scss'; // legacy bootstrap/scss bundle removed during UI V2 cutover
import './styles/figma-raw/v2.css'; // Theme V2 override (now global)
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
