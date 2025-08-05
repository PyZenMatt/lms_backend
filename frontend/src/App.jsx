import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { loadStripe } from '@stripe/stripe-js';
import { Elements } from '@stripe/react-stripe-js';

import routes, { renderRoutes } from './routes';
import NotificationDisplay from './components/ui/NotificationDisplay';
import { ThemeProvider } from './contexts/ThemeContext';

// Import development error handling
import './utils/errorHandling';

// Import mobile-responsive styles
import './styles/mobile-responsive.css';
// Import gas-free system styles
import './styles/gasFreeSystem.css';
// Import dark theme styles
import './assets/css/dark-theme.css';

// Initialize Stripe
const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY);

const App = () => {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Elements stripe={stripePromise}>
          {renderRoutes(routes)}
          <NotificationDisplay />
        </Elements>
      </BrowserRouter>
    </ThemeProvider>
  );
};

export default App;
