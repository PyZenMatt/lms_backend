import React from 'react';
import { createRoot } from 'react-dom/client';

import { ConfigProvider } from './contexts/ConfigContext';
import { AuthProvider } from './contexts/AuthContext';
import { Web3Provider } from './contexts/Web3Context';
import { NotificationProvider } from './contexts/NotificationContext';

// Ensure theme attribute is present before any component logic (SSR-friendly if added server side)
document.documentElement.setAttribute('data-theme', 'v2');

// Base token layer (old tokens) then override with V2 semantic layer
import './styles/tokens.css';
import './styles/figma-raw/v2.css'; // Theme V2 override
// import './index.scss'; // legacy bootstrap/scss bundle removed during UI V2 cutover
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
