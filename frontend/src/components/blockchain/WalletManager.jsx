import React, { useState, useEffect } from 'react';
import { Card, Button, Alert, Modal, Form, Badge, Spinner, Row, Col } from 'react-bootstrap';
import { web3Service } from '../../services/api/web3Service';
import { blockchainAPI } from '../../services/api/blockchainAPI';
import { useAuth } from '../../contexts/AuthContext';
import './WalletManager.scss';

const WalletManager = ({ onWalletConnected }) => {
  const { user } = useAuth();
  const [walletState, setWalletState] = useState({
    connected: false,
    address: null,
    generatedAddress: null,
    isLoading: false,
    error: null
  });
  
  const [showRecoveryModal, setShowRecoveryModal] = useState(false);
  const [showBackupModal, setShowBackupModal] = useState(false);
  const [recoveryPhrase, setRecoveryPhrase] = useState('');
  const [backupPhrase, setBackupPhrase] = useState('');
  const [isGeneratingWallet, setIsGeneratingWallet] = useState(false);

  useEffect(() => {
    checkWalletConnection();
  }, []);

  // Sincronizza con il wallet address dell'utente dal backend
  useEffect(() => {
    if (user?.wallet_address && !walletState.connected) {
      setWalletState(prev => ({
        ...prev,
        connected: true,
        address: user.wallet_address,
        isLoading: false
      }));
      
      if (onWalletConnected) {
        onWalletConnected(user.wallet_address);
      }
    }
  }, [user?.wallet_address, walletState.connected, onWalletConnected]);

  const checkWalletConnection = async () => {
    try {
      setWalletState(prev => ({ ...prev, isLoading: true }));
      
      // Check if MetaMask is installed
      if (!web3Service.isMetamaskInstalled()) {
        // Check if user has a generated wallet
        const savedAddress = localStorage.getItem('connectedWalletAddress');
        const generatedAddress = localStorage.getItem('generatedWalletAddress');
        
        if (savedAddress || generatedAddress) {
          setWalletState(prev => ({
            ...prev,
            connected: true,
            address: savedAddress,
            generatedAddress: generatedAddress,
            isLoading: false
          }));
          
          if (onWalletConnected) {
            onWalletConnected(savedAddress || generatedAddress);
          }
        } else {
          setWalletState(prev => ({
            ...prev,
            isLoading: false,
            error: 'MetaMask non installato. Puoi generare un wallet automatico.'
          }));
        }
        return;
      }

      // Check MetaMask connection
      const connected = await web3Service.isConnected();
      if (connected) {
        const address = await web3Service.getCurrentAccount();
        setWalletState(prev => ({
          ...prev,
          connected: true,
          address: address,
          isLoading: false
        }));
        
        if (onWalletConnected) {
          onWalletConnected(address);
        }
      } else {
        setWalletState(prev => ({ ...prev, isLoading: false }));
      }
    } catch (error) {
      console.error('Error checking wallet connection:', error);
      setWalletState(prev => ({
        ...prev,
        isLoading: false,
        error: 'Errore nella verifica del wallet'
      }));
    }
  };

  const connectMetaMask = async () => {
    try {
      setWalletState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const address = await web3Service.connectWallet();
      await blockchainAPI.linkWallet(address);
      
      setWalletState(prev => ({
        ...prev,
        connected: true,
        address: address,
        isLoading: false
      }));
      
      localStorage.setItem('connectedWalletAddress', address);
      
      if (onWalletConnected) {
        onWalletConnected(address);
      }
    } catch (error) {
      console.error('Error connecting wallet:', error);
      setWalletState(prev => ({
        ...prev,
        isLoading: false,
        error: error.message || 'Errore nella connessione del wallet'
      }));
    }
  };

  const generateWallet = async () => {
    try {
      setIsGeneratingWallet(true);
      
      // Generate new wallet using web3
      const wallet = web3Service.generateWallet();
      
      // Link wallet with backend
      await blockchainAPI.linkWallet(wallet.address);
      
      setWalletState(prev => ({
        ...prev,
        connected: true,
        generatedAddress: wallet.address,
        isLoading: false
      }));
      
      // Store wallet info securely
      localStorage.setItem('generatedWalletAddress', wallet.address);
      localStorage.setItem('connectedWalletAddress', wallet.address);
      
      // Show backup phrase
      setBackupPhrase(wallet.mnemonic);
      setShowBackupModal(true);
      
      if (onWalletConnected) {
        onWalletConnected(wallet.address);
      }
    } catch (error) {
      console.error('Error generating wallet:', error);
      setWalletState(prev => ({
        ...prev,
        error: error.message || 'Errore nella generazione del wallet'
      }));
    } finally {
      setIsGeneratingWallet(false);
    }
  };

  const recoverWallet = async () => {
    try {
      if (!recoveryPhrase.trim()) {
        setWalletState(prev => ({ ...prev, error: 'Inserisci la frase di recupero' }));
        return;
      }

      setWalletState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const wallet = web3Service.recoverWallet(recoveryPhrase.trim());
      await blockchainAPI.linkWallet(wallet.address);
      
      setWalletState(prev => ({
        ...prev,
        connected: true,
        generatedAddress: wallet.address,
        isLoading: false
      }));
      
      localStorage.setItem('generatedWalletAddress', wallet.address);
      localStorage.setItem('connectedWalletAddress', wallet.address);
      
      setShowRecoveryModal(false);
      setRecoveryPhrase('');
      
      if (onWalletConnected) {
        onWalletConnected(wallet.address);
      }
    } catch (error) {
      console.error('Error recovering wallet:', error);
      setWalletState(prev => ({
        ...prev,
        isLoading: false,
        error: 'Frase di recupero non valida'
      }));
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const formatAddress = (address) => {
    if (!address) return '';
    return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
  };

  const currentAddress = walletState.address || walletState.generatedAddress;

  return (
    <div className="wallet-manager">
      {walletState.error && (
        <Alert variant="danger" className="error-alert">
          <i className="feather icon-alert-triangle me-2"></i>
          {walletState.error}
        </Alert>
      )}

      <Row>
        {walletState.connected ? (
          <>
            {/* Wallet Status Card */}
            <Col md={6} className="mb-4">
              <Card className="wallet-status-card h-100">
                <Card.Body>
                  <div className="d-flex justify-content-between align-items-start mb-3">
                    <Card.Title className="h6 text-muted mb-0">
                      Stato Wallet
                    </Card.Title>
                    <Badge bg="success">
                      <i className="feather icon-check me-1"></i>
                      Connesso
                    </Badge>
                  </div>
                  
                  <div className="wallet-address-display">
                    <div className="d-flex justify-content-between align-items-center">
                      <div>
                        <div className="address-label">
                          <small>Indirizzo Wallet:</small>
                        </div>
                        <div className="address-value">
                          {formatAddress(currentAddress)}
                        </div>
                      </div>
                      <Button
                        variant="outline-secondary"
                        size="sm"
                        className="copy-btn"
                        onClick={() => copyToClipboard(currentAddress)}
                      >
                        <i className="feather icon-copy"></i>
                      </Button>
                    </div>
                  </div>

                  <div className="network-info">
                    <small>
                      <i className="feather icon-globe"></i>
                      Rete: Polygon Amoy Testnet
                    </small>
                  </div>
                </Card.Body>
              </Card>
            </Col>

            {/* Wallet Actions Card */}
            <Col md={6} className="mb-4">
              <Card className="wallet-actions-card h-100">
                <Card.Body>
                  <Card.Title className="h6 text-muted mb-3">
                    Azioni Wallet
                  </Card.Title>
                  
                  {walletState.generatedAddress && (
                    <Button
                      variant="outline-warning"
                      className="w-100 mb-3"
                      onClick={() => setShowBackupModal(true)}
                    >
                      <i className="feather icon-download me-1"></i>
                      Backup Wallet
                    </Button>
                  )}

                  <div className="network-info">
                    <div className="info-row">
                      <span className="label">Rete:</span>
                      <span className="value">Polygon Amoy</span>
                    </div>
                  </div>
                </Card.Body>
              </Card>
            </Col>
          </>
        ) : (
          <>
            {/* MetaMask Connection Card */}
            <Col md={6} className="mb-4">
              <Card className="connection-card h-100">
                <Card.Body>
                  <Card.Title className="h6 text-muted mb-3">
                    <i className="feather icon-link me-2"></i>
                    Connetti MetaMask
                  </Card.Title>
                  
                  {web3Service.isMetamaskInstalled() ? (
                    <Button
                      variant="primary"
                      className="w-100"
                      onClick={connectMetaMask}
                      disabled={walletState.isLoading}
                    >
                      {walletState.isLoading ? (
                        <>
                          <Spinner animation="border" size="sm" className="me-2" />
                          Connessione...
                        </>
                      ) : (
                        <>
                          <i className="feather icon-link me-2"></i>
                          Connetti MetaMask
                        </>
                      )}
                    </Button>
                  ) : (
                    <div className="metamask-info">
                      <div className="mb-3">
                        <small className="text-muted">
                          MetaMask non è installato nel tuo browser
                        </small>
                      </div>
                      <Button
                        variant="outline-primary"
                        className="w-100"
                        as="a"
                        href="https://metamask.io/"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <i className="feather icon-external-link me-2"></i>
                        Installa MetaMask
                      </Button>
                    </div>
                  )}
                </Card.Body>
              </Card>
            </Col>

            {/* Alternative Options Card */}
            <Col md={6} className="mb-4">
              <Card className="connection-card h-100">
                <Card.Body>
                  <Card.Title className="h6 text-muted mb-3">
                    <i className="feather icon-settings me-2"></i>
                    Opzioni Alternative
                  </Card.Title>
                  
                  <Button
                    variant="success"
                    className="w-100 mb-3"
                    onClick={generateWallet}
                    disabled={isGeneratingWallet}
                  >
                    {isGeneratingWallet ? (
                      <>
                        <Spinner animation="border" size="sm" className="me-2" />
                        Generazione...
                      </>
                    ) : (
                      <>
                        <i className="feather icon-plus me-2"></i>
                        Genera Wallet
                      </>
                    )}
                  </Button>

                  <Button
                    variant="outline-secondary"
                    className="w-100"
                    onClick={() => setShowRecoveryModal(true)}
                  >
                    <i className="feather icon-refresh-cw me-2"></i>
                    Recupera Wallet
                  </Button>
                </Card.Body>
              </Card>
            </Col>
          </>
        )}
      </Row>

      {/* Recovery Modal */}
      <Modal show={showRecoveryModal} onHide={() => setShowRecoveryModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Recupera Wallet</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Frase di Recupero (12 parole)</Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                value={recoveryPhrase}
                onChange={(e) => setRecoveryPhrase(e.target.value)}
                placeholder="Inserisci le 12 parole separate da spazi..."
              />
              <Form.Text className="text-muted">
                Inserisci la frase di recupero di 12 parole del tuo wallet.
              </Form.Text>
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowRecoveryModal(false)}>
            Annulla
          </Button>
          <Button 
            variant="primary" 
            onClick={recoverWallet}
            disabled={walletState.isLoading}
          >
            {walletState.isLoading ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Recupero...
              </>
            ) : (
              'Recupera Wallet'
            )}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Backup Modal */}
      <Modal show={showBackupModal} onHide={() => setShowBackupModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>
            <i className="feather icon-shield me-2 text-warning"></i>
            Backup Wallet
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Alert variant="warning">
            <strong>IMPORTANTE:</strong> Salva questa frase di recupero in un posto sicuro. 
            È l'unico modo per recuperare il tuo wallet se perdi l'accesso.
          </Alert>
          
          {backupPhrase && (
            <div className="backup-phrase bg-light p-3 rounded mb-3">
              <div className="d-flex justify-content-between align-items-start mb-2">
                <small className="text-muted">Frase di Recupero:</small>
                <Button
                  variant="outline-secondary"
                  size="sm"
                  onClick={() => copyToClipboard(backupPhrase)}
                >
                  <i className="feather icon-copy"></i>
                </Button>
              </div>
              <code className="user-select-all">{backupPhrase}</code>
            </div>
          )}
          
          <Alert variant="info">
            <small>
              <i className="feather icon-info me-1"></i>
              Questa frase non verrà più mostrata. Assicurati di averla salvata!
            </small>
          </Alert>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="primary" onClick={() => setShowBackupModal(false)}>
            Ho Salvato la Frase
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default WalletManager;
