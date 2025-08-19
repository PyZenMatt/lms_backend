/* @ts-nocheck */
import React, { useEffect } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { loadStripe } from '@stripe/stripe-js';
import { Elements } from '@stripe/react-stripe-js';

import routes, { renderRoutes } from './routes';
import NotificationDisplay from './components/ui/ui-legacy/NotificationDisplay';
import { ThemeProvider } from './contexts/ThemeContext';
import { AppShell } from './components/layout/AppShell';

// Import development error handling
import './utils/errorHandling';

// Initialize Stripe
const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY);

const App = () => {
  useEffect(() => {
    if (!document.title || document.title.includes('Datta')) {
      document.title = 'SchoolPlatform';
    }
  }, []);
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AppShell>
          <Elements stripe={stripePromise}>
            {renderRoutes(routes)}
            <NotificationDisplay />
          </Elements>
        </AppShell>
      </BrowserRouter>
    </ThemeProvider>
  );
};

export default App;
