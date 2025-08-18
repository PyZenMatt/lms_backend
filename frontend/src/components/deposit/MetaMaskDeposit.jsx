/**
 * 🔄 MetaMask Deposit Component
 *
 * Handles MetaMask → Platform balance transfers
 * Uses existing BurnDepositInterface
 */

import React, { useState } from 'react';
import { Card, Alert } from '@/components/ui';
import BurnDepositInterface from '../blockchain/BurnDepositInterface';

const MetaMaskDeposit = ({ onDepositComplete }) => {
  const [success, setSuccess] = useState('');

  const handleDepositComplete = () => {
    setSuccess('Deposit completed! Your platform balance has been updated.');
    if (onDepositComplete) {
      onDepositComplete();
    }
  };

  return (
    <Card className="metamask-deposit-bg-bg-card text-card-foreground rounded-lg border border-border shadow-sm text-bg-card text-card-foreground rounded-lg border border-border shadow-sm-foreground border border-border rounded-lg shadow-sm">
      <Card.Header className="bg-gradient-warning text-hsl(var(--background))">
        <h5 className="mb-0">
          <i className="fab fa-ethereum me-2"></i>
          Deposit TEO from MetaMask
          <span className="inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium bg-accent text-accent-foreground bg-light text-dark ms-2">MetaMask → Platform</span>
        </h5>
      </Card.Header>

      <Card.Body>
        {success && (
          <Alert variant="success" dismissible onClose={() => setSuccess('')}>
            <i className="feather icon-check-circle me-2"></i>
            {success}
          </Alert>
        )}

        {/* Use existing BurnDepositInterface */}
        <BurnDepositInterface onTransactionComplete={handleDepositComplete} />
      </Card.Body>
    </Card>
  );
};

export default MetaMaskDeposit;
