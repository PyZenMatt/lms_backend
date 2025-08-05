import React, { useState, useEffect } from 'react';
import { Card, Spinner, Badge, Button, Modal, Form, Alert } from 'react-bootstrap';
import { useAuth } from '../../contexts/AuthContext';
import PendingWithdrawals from './PendingWithdrawals';

/**
 * Updated TeoCoinBalance component using DB-based system
 * Replaces blockchain calls with fast database operations
 * Includes withdrawal functionality to MetaMask
 */
const DBTeoCoinBalance = ({ title = "Saldo TeoCoin", showDetails = false, showWithdrawal = true }) => {
  const { user: currentUser } = useAuth();
  const [balance, setBalance] = useState({
    available_balance: 0,
    staked_balance: 0,
    pending_withdrawal: 0,
    total_balance: 0
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Withdrawal modal state
  const [showWithdrawalModal, setShowWithdrawalModal] = useState(false);
  const [withdrawalAmount, setWithdrawalAmount] = useState('');
  const [withdrawalAddress, setWithdrawalAddress] = useState('');
  const [withdrawalLoading, setWithdrawalLoading] = useState(false);
  const [withdrawalError, setWithdrawalError] = useState('');
  
  // Pending withdrawals state
  const [showPendingWithdrawals, setShowPendingWithdrawals] = useState(false);

  // Fetch DB-based balance
  const fetchBalance = async () => {
    if (!currentUser) return;
    
    setLoading(true);
    setError('');
    
    try {
      // Use withdrawal API for consistency
      const response = await fetch('/api/v1/teocoin/withdrawals/balance/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Balance API error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('🔍 DBTeoCoinBalance API Response:', data);
      
      if (data.success && data.balance) {
        // Convert withdrawal API format to component format
        setBalance({
          available_balance: parseFloat(data.balance.available || 0),
          staked_balance: parseFloat(data.balance.staked || 0),
          pending_withdrawal: parseFloat(data.balance.pending_withdrawal || 0),
          total_balance: parseFloat(data.balance.total || 0)
        });
      } else {
        console.warn('Balance API returned no data:', data);
        setBalance({
          available_balance: 0,
          staked_balance: 0,
          pending_withdrawal: 0,
          total_balance: 0
        });
      }
    } catch (err) {
      console.error('Error fetching DB balance:', err);
      setError('Errore nel caricamento saldo');
      setBalance({
        available_balance: 0,
        staked_balance: 0,
        pending_withdrawal: 0,
        total_balance: 0
      });
    } finally {
      setLoading(false);
    }
  };

  // Handle withdrawal request
  const handleWithdrawalRequest = async () => {
    if (!withdrawalAmount || !withdrawalAddress) {
      setWithdrawalError('Inserisci importo e indirizzo wallet');
      return;
    }

    const amount = parseFloat(withdrawalAmount);
    if (amount <= 0 || amount > balance.available_balance) {
      setWithdrawalError('Importo non valido o saldo insufficiente');
      return;
    }

    setWithdrawalLoading(true);
    setWithdrawalError('');

    try {
      const response = await fetch('/api/v1/teocoin/withdraw/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          amount: amount,
          wallet_address: withdrawalAddress
        })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Check if withdrawal was auto-processed
        if (data.auto_processed && data.status === 'completed') {
          // Auto-processed successfully!
          setSuccess(`🎉 ${data.amount} TEO minted successfully to your MetaMask wallet! TX: ${data.transaction_hash?.substring(0, 10)}...`);
        } else if (data.status === 'completed') {
          // Completed normally
          setSuccess(`✅ ${data.amount} TEO withdrawal completed! TX: ${data.transaction_hash?.substring(0, 10)}...`);
        } else {
          // Still pending (fallback)
          setSuccess(`⏳ Withdrawal request created! ID: ${data.withdrawal_id} - Processing...`);
        }
        
        setShowWithdrawalModal(false);
        setWithdrawalAmount('');
        setWithdrawalAddress('');
        // Refresh balance
        fetchBalance();
      } else {
        throw new Error(data.error || 'Errore nella richiesta di prelievo');
      }
    } catch (err) {
      console.error('Error creating withdrawal:', err);
      setWithdrawalError(err.message);
    } finally {
      setWithdrawalLoading(false);
    }
  };

  // Auto-fill wallet address if available
  useEffect(() => {
    if (currentUser?.wallet_address) {
      setWithdrawalAddress(currentUser.wallet_address);
    }
  }, [currentUser]);

  // Fetch balance on component mount
  useEffect(() => {
    if (currentUser) {
      fetchBalance();
    }
  }, [currentUser]);

  const formatAddress = (address) => {
    if (!address) return '';
    return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
  };

  return (
    <>
      <Card className="h-100">
        <Card.Body>
          <div className="d-flex justify-content-between align-items-start mb-3">
            <Card.Title className="h6 text-muted mb-0">
              {title}
            </Card.Title>
            
            <Badge bg="info" className="d-flex align-items-center">
              <i className="feather icon-database me-1" style={{ fontSize: '12px' }}></i>
              DB System
            </Badge>
          </div>

          <div className="mb-3">
            <div className="h3 fw-bold text-primary d-flex align-items-baseline">
              {loading ? (
                <Spinner animation="border" size="sm" className="text-primary" />
              ) : (
                <>
                  {balance.total_balance}
                  <span className="text-muted ms-2">
                    TEO
                  </span>
                </>
              )}
            </div>
            
            <small className="text-muted">
              Database • Instant Operations
            </small>
          </div>

          {showDetails && (
            <div className="small text-muted mb-3">
              <div className="row g-2">
                <div className="col-6">
                  <div className="bg-success bg-opacity-10 p-2 rounded text-center">
                    <div className="fw-bold text-success">{balance.available_balance}</div>
                    <div className="small text-muted">Disponibile</div>
                  </div>
                </div>
                <div className="col-6">
                  <div className="bg-primary bg-opacity-10 p-2 rounded text-center">
                    <div className="fw-bold text-primary">{balance.staked_balance}</div>
                    <div className="small text-muted">Staked</div>
                  </div>
                </div>
              </div>
              
              {balance.pending_withdrawal > 0 && (
                <div className="mt-2">
                  <div className="bg-warning bg-opacity-10 p-2 rounded text-center">
                    <div className="fw-bold text-warning">{balance.pending_withdrawal}</div>
                    <div className="small text-muted">Prelievo Pending</div>
                  </div>
                </div>
              )}
            </div>
          )}

          {error && (
            <Alert variant="danger" className="py-2 small">
              {error}
            </Alert>
          )}

          {success && (
            <Alert variant="success" className="py-2 small">
              {success}
            </Alert>
          )}

          <div className="d-grid gap-2">
            <Button 
              variant="outline-primary" 
              size="sm" 
              onClick={fetchBalance}
              disabled={loading}
            >
              <i className="feather icon-refresh-cw me-1"></i>
              Aggiorna
            </Button>
            
            {showWithdrawal && balance.available_balance > 0 && (
              <Button 
                variant="outline-success" 
                size="sm" 
                onClick={() => setShowWithdrawalModal(true)}
              >
                <i className="feather icon-download me-1"></i>
                Preleva su MetaMask
              </Button>
            )}
            
            {/* Show Pending Withdrawals Button */}
            {balance.pending_withdrawal > 0 && (
              <Button 
                variant="warning" 
                size="sm" 
                onClick={() => setShowPendingWithdrawals(!showPendingWithdrawals)}
              >
                <i className="feather icon-clock me-1"></i>
                {showPendingWithdrawals ? 'Nascondi' : 'Processa'} Prelievi Pending
              </Button>
            )}
          </div>

          <div className="mt-3 small text-muted">
            <div className="d-flex justify-content-between">
              <span>Sistema:</span>
              <span>Database</span>
            </div>
            <div className="d-flex justify-content-between">
              <span>Costo Gas:</span>
              <span className="text-success">Gratuito ✨</span>
            </div>
            <div className="d-flex justify-content-between">
              <span>Velocità:</span>
              <span className="text-primary">Istantaneo ⚡</span>
            </div>
          </div>
        </Card.Body>
      </Card>

      {/* Pending Withdrawals Section */}
      {showPendingWithdrawals && (
        <div className="mt-3">
          <PendingWithdrawals 
            onTransactionComplete={(data) => {
              // Refresh balance when transaction completes
              fetchBalance();
              setSuccess(`✅ ${data.amount_minted} TEO minted successfully! TX: ${data.transaction_hash?.substring(0, 10)}...`);
              setTimeout(() => setSuccess(''), 5000);
            }}
          />
        </div>
      )}

      {/* Withdrawal Modal */}
      <Modal show={showWithdrawalModal} onHide={() => setShowWithdrawalModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>
            <i className="feather icon-download me-2"></i>
            Preleva TEO su MetaMask
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="mb-3">
            <div className="bg-info bg-opacity-10 p-3 rounded">
              <h6 className="text-info mb-2">
                <i className="feather icon-info me-2"></i>
                Come Funziona il Prelievo
              </h6>
              <ul className="small mb-0">
                <li>TEO viene trasferito dal database al tuo wallet MetaMask</li>
                <li>La piattaforma paga tutte le fee del gas (gratis per te!)</li>
                <li>Tempo di elaborazione: 5-10 minuti</li>
                <li>Riceverai veri token TEO sulla blockchain</li>
              </ul>
            </div>
          </div>

          <Form.Group className="mb-3">
            <Form.Label>Importo da Prelevare</Form.Label>
            <div className="input-group">
              <Form.Control
                type="number"
                value={withdrawalAmount}
                onChange={(e) => setWithdrawalAmount(e.target.value)}
                placeholder="Es. 100"
                min="0.01"
                max={balance.available_balance}
                step="0.01"
                disabled={withdrawalLoading}
              />
              <span className="input-group-text">TEO</span>
            </div>
            <Form.Text className="text-muted">
              Disponibile: {balance.available_balance} TEO
            </Form.Text>
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Indirizzo Wallet MetaMask</Form.Label>
            <Form.Control
              type="text"
              value={withdrawalAddress}
              onChange={(e) => setWithdrawalAddress(e.target.value)}
              placeholder="0x..."
              disabled={withdrawalLoading}
            />
            <Form.Text className="text-muted">
              {currentUser?.wallet_address ? 
                `Indirizzo dal profilo: ${formatAddress(currentUser.wallet_address)}` :
                'Inserisci l\'indirizzo del tuo wallet MetaMask'
              }
            </Form.Text>
          </Form.Group>

          {withdrawalError && (
            <Alert variant="danger" className="py-2">
              {withdrawalError}
            </Alert>
          )}

          <div className="bg-light p-3 rounded">
            <div className="d-flex justify-content-between small text-muted">
              <span>Costo Gas per te:</span>
              <span className="text-success fw-bold">Gratuito 🎉</span>
            </div>
            <div className="d-flex justify-content-between small text-muted">
              <span>Costo Gas Piattaforma:</span>
              <span>~$0.005 USD</span>
            </div>
            <div className="d-flex justify-content-between small text-muted">
              <span>Tempo di Elaborazione:</span>
              <span>5-10 minuti</span>
            </div>
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowWithdrawalModal(false)}>
            Annulla
          </Button>
          <Button 
            variant="primary" 
            onClick={handleWithdrawalRequest}
            disabled={withdrawalLoading || !withdrawalAmount || !withdrawalAddress}
          >
            {withdrawalLoading ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Elaborazione...
              </>
            ) : (
              <>
                <i className="feather icon-download me-2"></i>
                Conferma Prelievo
              </>
            )}
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
};

export default DBTeoCoinBalance;
