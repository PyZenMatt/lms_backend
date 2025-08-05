import React, { useState, useEffect } from 'react';
import { Card, Alert, Spinner, Badge } from 'react-bootstrap';
import { web3Service } from '../../services/api/web3Service';
import { useAuth } from '../../contexts/AuthContext';

const WalletBalanceDisplay = ({ balance = null, loading: externalLoading = false, isAdmin = false }) => {
  const { user } = useAuth();
  const [balances, setBalances] = useState({
    teocoin: balance || '0',
    matic: '0',
    loading: externalLoading,
    error: null
  });

  const loadBalances = async () => {
    if (!user?.wallet_address) {
      setBalances(prev => ({
        ...prev,
        loading: false,
        error: 'Nessun wallet collegato al profilo'
      }));
      return;
    }

    try {
      setBalances(prev => ({ ...prev, loading: true, error: null }));

      // Carica i saldi usando l'indirizzo dal profilo utente
      const [teoBalance, maticBalance] = await Promise.all([
        web3Service.getBalance(user.wallet_address),
        web3Service.getMaticBalance(user.wallet_address)
      ]);

      setBalances({
        teocoin: parseFloat(teoBalance).toFixed(2),
        matic: parseFloat(maticBalance).toFixed(4),
        loading: false,
        error: null
      });

      console.log('💰 Saldi caricati per wallet:', user.wallet_address);
      console.log('💰 TEO:', teoBalance, 'MATIC:', maticBalance);

    } catch (error) {
      console.error('Errore nel caricamento saldi:', error);
      setBalances(prev => ({
        ...prev,
        loading: false,
        error: 'Errore nel caricamento dei saldi'
      }));
    }
  };

  useEffect(() => {
    if (balance !== null) {
      // Se è fornito un balance esterno, usalo
      setBalances(prev => ({
        ...prev,
        teocoin: balance,
        loading: externalLoading
      }));
    } else {
      // Altrimenti carica i saldi normalmente
      loadBalances();
    }
  }, [user?.wallet_address, balance, externalLoading]);

  const formatAddress = (address) => {
    if (!address) return '';
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  if (!user?.wallet_address) {
    return (
      <Card className="wallet-balance-card">
        <Card.Body className="text-center">
          <i className="feather icon-wallet text-muted mb-3" style={{ fontSize: '2rem' }}></i>
          <h6 className="text-muted">Nessun Wallet Collegato</h6>
          <p className="text-muted small">
            Collega un wallet dal tuo profilo per visualizzare i saldi
          </p>
        </Card.Body>
      </Card>
    );
  }

  return (
    <Card className="wallet-balance-card">
      <Card.Body>
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h6 className="mb-0">
            <i className="feather icon-wallet me-2"></i>
            {isAdmin ? 'Saldi Admin' : 'Saldi Wallet'}
          </h6>
          <Badge bg="success" className="px-2 py-1">
            <i className="feather icon-link me-1"></i>
            Collegato
          </Badge>
        </div>

        <div className="mb-3">
          <div className="text-muted small mb-1">Indirizzo:</div>
          <code className="bg-light p-1 rounded small">
            {formatAddress(user.wallet_address)}
          </code>
        </div>

        {balances.error ? (
          <Alert variant="warning" className="py-2 mb-0">
            <small>{balances.error}</small>
          </Alert>
        ) : balances.loading ? (
          <div className="text-center py-3">
            <Spinner animation="border" size="sm" className="me-2" />
            <span className="text-muted">Caricamento saldi...</span>
          </div>
        ) : (
          <div className="row g-2">
            <div className="col-6">
              <div className="bg-primary bg-opacity-10 p-3 rounded text-center">
                <div className="text-primary fw-bold fs-5">{balances.teocoin}</div>
                <div className="text-muted small">TEO</div>
              </div>
            </div>
            <div className="col-6">
              <div className="bg-secondary bg-opacity-10 p-3 rounded text-center">
                <div className="text-secondary fw-bold fs-6">{balances.matic}</div>
                <div className="text-muted small">MATIC</div>
              </div>
            </div>
          </div>
        )}
      </Card.Body>
    </Card>
  );
};

export default WalletBalanceDisplay;
