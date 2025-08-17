/**
 * 🔄 MetaMask Deposit Component
 *
 * Handles MetaMask → Platform balance transfers
 * Uses existing BurnDepositInterface
 */

import React, { useState } from 'react';
import { Card, Alert } from 'react-bootstrap';
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
    <Card className="metamask-deposit-card">
      <Card.Header className="bg-gradient-warning text-white">
        <h5 className="mb-0">
          <i className="fab fa-ethereum me-2"></i>
          Deposit TEO from MetaMask
          <span className="badge bg-light text-dark ms-2">MetaMask → Platform</span>
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
