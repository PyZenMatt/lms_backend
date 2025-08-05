import React, { useState, useEffect } from 'react';
import { Card, Button, Alert, Badge } from 'react-bootstrap';
import { web3Service } from '../../services/api/web3Service';
import { useAuth } from '../../contexts/AuthContext';
import { connectWallet, disconnectWallet } from '../../services/api/dashboard';
import './WalletManager.scss';

const ProfileWalletDisplay = ({ 
  onWalletConnected, 
  walletAddress = null, 
  teocoins = null, 
  loading: externalLoading = false, 
  isAdmin = false 
}) => {
  const { user, refreshUser } = useAuth();
  const [walletState, setWalletState] = useState({
    connected: walletAddress ? true : false,
    address: walletAddress || null,
    isLoading: externalLoading,
    error: null
  });

  useEffect(() => {
    // Se sono forniti parametri esterni (per admin), usali
    if (walletAddress !== null) {
      setWalletState({
        connected: true,
        address: walletAddress,
        isLoading: externalLoading,
        error: null
      });
      return;
    }

    // Se l'utente ha già un wallet connesso nel database, ripristina lo stato bloccato
    if (user?.wallet_address) {
      setWalletState({
        connected: true,
        address: user.wallet_address,
        isLoading: false,
        error: null
      });
      
      // Ripristina lo stato bloccato nel web3Service se necessario
      if (!web3Service.isWalletLockedToAddress()) {
        console.log('🔄 Ripristino stato wallet dal database:', user.wallet_address);
        // Simula una connessione per bloccare il wallet a questo indirizzo
        web3Service.isWalletLocked = true;
        web3Service.lockedWalletAddress = user.wallet_address;
        web3Service.userAddress = user.wallet_address;
        
        // Salva in localStorage
        localStorage.setItem('isWalletLocked', 'true');
        localStorage.setItem('lockedWalletAddress', user.wallet_address);
        localStorage.setItem('connectedWalletAddress', user.wallet_address);
      }
      
      if (onWalletConnected) {
        onWalletConnected(user.wallet_address);
      }
    } else {
      // Nessun wallet nel database - assicurati che web3Service sia disconnesso
      if (web3Service.isWalletLockedToAddress()) {
        web3Service.disconnectWallet();
      }
    }
  }, [user?.wallet_address, onWalletConnected, walletAddress, externalLoading]);

  const connectWalletHandler = async () => {
    try {
      setWalletState(prev => ({ ...prev, isLoading: true, error: null }));
      
      if (!web3Service.isMetamaskInstalled()) {
        throw new Error('MetaMask non è installato. Scarica MetaMask per continuare.');
      }

      // Connetti tramite web3Service (questo blocca il wallet)
      const walletAddress = await web3Service.connectWallet();
      if (!walletAddress) {
        throw new Error('Nessun account trovato. Assicurati di essere connesso a MetaMask.');
      }
      
      console.log('🔗 Connessione wallet completata:', walletAddress);
      
      // Salva nel database tramite API
      await connectWallet(walletAddress);
      
      // Aggiorna il contesto utente
      await refreshUser();
      
      setWalletState({
        connected: true,
        address: walletAddress,
        isLoading: false,
        error: null
      });

      if (onWalletConnected) {
        onWalletConnected(walletAddress);
      }
      
    } catch (error) {
      console.error('Connection error:', error);
      setWalletState(prev => ({
        ...prev,
        isLoading: false,
        error: error.message || 'Errore durante la connessione del wallet'
      }));
    }
  };

  const disconnectWalletHandler = async () => {
    try {
      setWalletState(prev => ({ ...prev, isLoading: true, error: null }));
      
      console.log('🔓 Disconnessione wallet in corso...');
      
      // Disconnetti dal web3Service (questo rimuove il lock)
      web3Service.disconnectWallet();
      
      // Rimuovi dal database tramite API
      await disconnectWallet();
      
      // Aggiorna il contesto utente
      await refreshUser();
      
      setWalletState({
        connected: false,
        address: null,
        isLoading: false,
        error: null
      });

      if (onWalletConnected) {
        onWalletConnected(null);
      }
      
      console.log('✅ Wallet disconnesso correttamente');
      
    } catch (error) {
      console.error('Disconnect error:', error);
      setWalletState(prev => ({
        ...prev,
        isLoading: false,
        error: error.message || 'Errore durante la disconnessione del wallet'
      }));
    }
  };

  const formatAddress = (address) => {
    if (!address) return '';
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  return (
    <Card className="wallet-status-card">
      <Card.Body>
        <Card.Title>
          <i className="feather icon-wallet me-2"></i>
          {isAdmin ? 'Wallet Admin' : 'Wallet Connesso'}
        </Card.Title>
        
        {walletState.error && (
          <Alert variant="danger" className="mb-3">
            {walletState.error}
          </Alert>
        )}

        {walletState.connected ? (
          <div className="text-center">
            <Badge bg="success" className="mb-3 d-flex align-items-center justify-content-center p-2">
              <i className="feather icon-check me-2"></i>
              Wallet Connesso
            </Badge>
            
            <div className="mb-3">
              <h6 className="text-muted mb-2">Indirizzo:</h6>
              <div className="d-flex align-items-center justify-content-center">
                <code className="bg-light p-2 rounded me-2">
                  {formatAddress(walletState.address)}
                </code>
                <Button
                  variant="outline-secondary"
                  size="sm"
                  onClick={() => navigator.clipboard.writeText(walletState.address)}
                  title="Copia indirizzo"
                >
                  <i className="feather icon-copy"></i>
                </Button>
              </div>
            </div>

            <div className="d-grid gap-2">
              <Button 
                variant="outline-danger" 
                onClick={disconnectWalletHandler}
                disabled={walletState.isLoading}
                size="sm"
              >
                {walletState.isLoading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                    Disconnettendo...
                  </>
                ) : (
                  <>
                    <i className="feather icon-x me-2"></i>
                    Disconnetti Wallet
                  </>
                )}
              </Button>
            </div>
          </div>
        ) : (
          <div className="text-center">
            <div className="mb-3">
              <i className="feather icon-wallet text-muted" style={{ fontSize: '3rem' }}></i>
            </div>
            <p className="text-muted mb-3">
              Connetti il tuo wallet per visualizzare l'indirizzo
            </p>
            <div className="d-grid">
              <Button 
                variant="primary" 
                onClick={connectWalletHandler}
                disabled={walletState.isLoading}
              >
                {walletState.isLoading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                    Connettendo...
                  </>
                ) : (
                  <>
                    <i className="feather icon-link me-2"></i>
                    Connetti Wallet
                  </>
                )}
              </Button>
            </div>
          </div>
        )}
      </Card.Body>
    </Card>
  );
};

export default ProfileWalletDisplay;
