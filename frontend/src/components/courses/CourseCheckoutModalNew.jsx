import React, { useState } from 'react';
import { Modal, Button, Alert, Spinner, Nav, Tab } from 'react-bootstrap';
import { purchaseCourse } from '../../services/api/courses';
import { web3Service } from '../../services/api/web3Service';
import { useAuth } from '../../contexts/AuthContext';
import PaymentModal from '../modals/PaymentModal';

/**
 * Enhanced CourseCheckoutModal - Supports both Stripe and TeoCoin payments
 * 
 * This component provides two payment options:
 * 1. Fiat payment via Stripe (EUR) with TeoCoin rewards
 * 2. TeoCoin payment with discount (existing blockchain flow)
 */
const CourseCheckoutModal = ({ course, show, handleClose, onPurchaseComplete }) => {
  const { user } = useAuth();
  console.log('🔥 CourseCheckoutModal RENDER:', { course: course?.id, show, walletAddress: user?.wallet_address });
  const [activeTab, setActiveTab] = useState('fiat'); // 'fiat' or 'teocoin'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState('confirm'); // confirm, purchasing, success
  const [blockchainBalance, setBlockchainBalance] = useState(0);
  const [maticBalance, setMaticBalance] = useState(0);
  const [transactionHash, setTransactionHash] = useState('');
  const [paymentResult, setPaymentResult] = useState(null);

  // Wallet connection status
  const walletConnected = Boolean(user?.wallet_address);
  const walletAddress = user?.wallet_address;

  // Calculate pricing options with REASONABLE TEO pricing
  const fiatPrice = course?.price_eur || 0;
  const teoReward = course?.teocoin_reward || 0;
  const teoDiscount = course?.teocoin_discount_percent || 10;
  
  // FIXED: Use 1 EUR = 1 TEO ratio (not 10x)
  const teoPrice = fiatPrice; // 1:1 ratio instead of 10x
  const discountedTeoPrice = teoPrice * (1 - teoDiscount / 100); // Apply discount
  
  console.log(`💰 Pricing: €${fiatPrice} = ${teoPrice} TEO, with ${teoDiscount}% discount = ${discountedTeoPrice.toFixed(2)} TEO`);

  // Load balances when modal opens (for TeoCoin tab)
  React.useEffect(() => {
    const loadBalances = async () => {
      if (!show || !walletAddress || activeTab !== 'teocoin') return;
      
      try {
        console.log('💰 Loading balances for wallet:', walletAddress);
        
        const [teoBalance, maticBalanceData] = await Promise.all([
          web3Service.getBalance(walletAddress),
          web3Service.getMaticBalance(walletAddress)
        ]);
        
        setBlockchainBalance(parseFloat(teoBalance));
        setMaticBalance(parseFloat(maticBalanceData));
        
        console.log('💰 Balances loaded - TEO:', teoBalance, 'MATIC:', maticBalanceData);
        
      } catch (err) {
        console.error('Error loading balances:', err);
        if (err.message && err.message.includes('Nessun indirizzo wallet specificato')) {
          setError('Devi collegare un wallet dal tuo profilo prima di visualizzare i saldi');
        } else {
          setError('Errore nel caricamento dei saldi wallet');
        }
      }
    };
    
    if (show) {
      setError('');
      setStep('confirm');
      setPaymentResult(null);
      loadBalances();
    }
  }, [show, walletAddress, activeTab]);

  // Handle Stripe payment success
  const handleStripeSuccess = (result) => {
    console.log('🎉 Payment success handler called!');
    console.log('💳 Payment result:', result);
    
    setPaymentResult(result);
    setStep('success');
    
    console.log('✅ Step set to success, paymentResult set');
    
    if (onPurchaseComplete) {
      console.log('🔄 Calling onPurchaseComplete...');
      onPurchaseComplete();
    } else {
      console.log('⚠️ No onPurchaseComplete callback provided');
    }
  };

  // Handle Stripe payment error  
  const handleStripeError = (error) => {
    console.error('❌ Payment error handler called:', error);
    setError(error);
    setStep('confirm');
  };

  // PHASE 3.1: Consolidated TeoCoin Discount Flow - Use Backend API
  const handleTeoCoinDiscount = async () => {
    console.log('🔥 PHASE 3.1: TeoCoin discount - using backend API', {
      user: user?.wallet_address,
      course: course?.id,
      discount_percent: teoDiscount
    });
    
    if (!user?.wallet_address) {
      setError('Devi collegare un wallet dal tuo profilo prima di procedere con lo sconto');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      // PHASE 3.1: Call backend API instead of frontend logic
      const response = await fetch('/api/v1/services/gas-free/permit-discount/signatures/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
        },
        body: JSON.stringify({
          course_id: course.id,
          discount_percentage: teoDiscount,
          student_wallet: user.wallet_address
        })
      });
      
      const data = await response.json();
      console.log('📨 Backend response:', data);
      
      if (data.success) {
        console.log('✅ TeoCoin discount applied successfully!');
        
        // Store discount info and switch to Stripe payment
        const discountInfo = {
          teo_used: data.teo_amount,
          discount_amount_eur: data.discount_amount,
          final_price: data.final_price,
          request_id: data.request_id
        };
        
        // Switch to fiat payment with applied discount
        setActiveTab('fiat');
        // Pass discount info to parent for Stripe payment
        if (onPurchaseComplete) {
          onPurchaseComplete({
            type: 'discount_applied',
            discountInfo,
            nextStep: 'stripe_payment'
          });
        }
      } else {
        setError(data.error || 'Errore durante l\'applicazione dello sconto TeoCoin');
      }
    } catch (error) {
      console.error('❌ TeoCoin discount error:', error);
      setError('Errore di connessione durante l\'applicazione dello sconto');
    } finally {
      setLoading(false);
    }
  };

  const refreshBalances = async () => {
    if (!walletConnected || !walletAddress) return;
    
    try {
      const [teoBalance, maticBalanceData] = await Promise.all([
        web3Service.getBalance(walletAddress),
        web3Service.getMaticBalance(walletAddress)
      ]);
      
      setBlockchainBalance(parseFloat(teoBalance));
      setMaticBalance(parseFloat(maticBalanceData));
    } catch (err) {
      console.error('Error refreshing balances:', err);
    }
  };

  const renderFiatPaymentTab = () => {
    if (step === 'success' && paymentResult) {
      return (
        <div className="text-center p-4">
          <div className="mb-3 text-success">
            <i className="feather icon-check-circle" style={{ fontSize: '48px' }}></i>
          </div>
          <h5>Pagamento completato!</h5>
          <p>Hai acquistato con successo il corso "{course?.title}".</p>
          <div className="mb-3">
            <strong>€{fiatPrice}</strong> pagati
            <br />
            <span className="text-success">+{teoReward} TEO</span> guadagnati come ricompensa!
          </div>
          <Button variant="primary" onClick={handleClose}>
            Accedi al corso
          </Button>
        </div>
      );
    }

    return (
      <div className="p-3">
        <div className="payment-option-card mb-4 p-3" style={{ border: '2px solid #007bff', borderRadius: '8px', backgroundColor: '#f8f9ff' }}>
          <div className="d-flex justify-content-between align-items-center mb-2">
            <h5 className="mb-0 text-primary">💳 Pagamento con Carta</h5>
            <span className="badge badge-primary">Consigliato</span>
          </div>
          <div className="row">
            <div className="col-6">
              <strong>Prezzo: €{fiatPrice}</strong>
            </div>
            <div className="col-6 text-end">
              <span className="text-success">+{teoReward} TEO Reward</span>
            </div>
          </div>
          <small className="text-muted">
            Pagamento sicuro con Stripe. Ricevi {teoReward} TeoCoin come ricompensa al completamento del corso.
          </small>
        </div>

        {error && (
          <Alert variant="danger" className="mb-3">
            {error}
          </Alert>
        )}

        <PaymentModal
          isOpen={true}
          course={course}
          onPaymentSuccess={handleStripeSuccess}
          onError={handleStripeError}
          onClose={handleClose}
          discountInfo={step === 'discount_applied' ? paymentResult : null}
        />
      </div>
    );
  };

  const renderTeoCoinPaymentTab = () => {
    console.log('🔍 Button state:', {
      loading,
      walletConnected,
      blockchainBalance,
      teoNeeded: Math.floor(fiatPrice * teoDiscount / 100),
      disabled: loading || !walletConnected || blockchainBalance < Math.floor(fiatPrice * teoDiscount / 100)
    });
    
    if (step === 'purchasing') {
      return (
        <div className="text-center p-4">
          <Spinner animation="border" className="mb-3" />
          <p>Acquisto in corso...</p>
          <small className="text-muted">Non chiudere questa finestra</small>
        </div>
      );
    }

    if (step === 'success' && !paymentResult) {
      return (
        <div className="text-center p-4">
          <div className="mb-3 text-success">
            <i className="feather icon-check-circle" style={{ fontSize: '48px' }}></i>
          </div>
          <h5>Acquisto completato!</h5>
          <p>Hai acquistato con successo il corso "{course?.title}" con TeoCoin.</p>
          {transactionHash && (
            <div className="mb-3">
              <small className="text-muted">Hash transazione:</small>
              <br />
              <code className="text-break" style={{ fontSize: '12px' }}>
                {transactionHash}
              </code>
            </div>
          )}
          <Button variant="primary" onClick={handleClose}>
            Accedi al corso
          </Button>
        </div>
      );
    }

    return (
      <div className="p-3">
        <div className="payment-option-card mb-4 p-3" style={{ border: '2px solid #28a745', borderRadius: '8px', backgroundColor: '#f8fff9' }}>
          <div className="d-flex justify-content-between align-items-center mb-2">
            <h5 className="mb-0 text-success">🪙 Sconto TeoCoin</h5>
            <span className="badge badge-success">{teoDiscount}% Sconto</span>
          </div>
          <div className="row">
            <div className="col-6">
              <strong>Usa {Math.floor(fiatPrice * teoDiscount / 100)} TEO</strong>
              <br />
              <small className="text-muted">
                Per €{(fiatPrice * teoDiscount / 100).toFixed(2)} di sconto
              </small>
            </div>
            <div className="col-6 text-end">
              <span className="text-success">Prezzo finale: €{(fiatPrice - fiatPrice * teoDiscount / 100).toFixed(2)}</span>
            </div>
          </div>
          <small className="text-muted">
            Usa i tuoi TeoCoin per ottenere uno sconto, poi completa il pagamento con carta.
          </small>
        </div>

        {!walletConnected && (
          <Alert variant="warning">
            <strong>Wallet non collegato</strong>
            <br />
            Devi collegare un wallet dal tuo profilo per procedere con il pagamento TeoCoin.
          </Alert>
        )}

        {walletConnected && (
          <div className="wallet-info mb-3 p-3" style={{ backgroundColor: '#f8f9fa', borderRadius: '6px' }}>
            <h6>💼 Saldo Wallet</h6>
            <div className="row">
              <div className="col-6">
                <span className="text-muted">TEO:</span> <strong>{blockchainBalance.toFixed(2)}</strong>
              </div>
              <div className="col-6">
                <span className="text-muted">Gas:</span> <strong style={{color: '#4CAF50'}}>🚀 Layer 2 (Free)</strong>
              </div>
            </div>
            <div className="mt-2">
              <small className="text-muted">
                Necessari: {Math.floor(fiatPrice * teoDiscount / 100)} TEO per {teoDiscount}% di sconto
              </small>
            </div>
            <Button variant="outline-secondary" size="sm" onClick={refreshBalances} className="mt-2">
              🔄 Aggiorna saldi
            </Button>
          </div>
        )}

        {error && (
          <Alert variant="danger" className="mb-3">
            {error}
          </Alert>
        )}

        <div className="d-grid">
          <Button
            variant="success"
            size="lg"
            onClick={() => {
              console.log('🔥 BUTTON CLICKED!');
              handleTeoCoinDiscount();
            }}
            disabled={loading || !walletConnected || blockchainBalance < Math.floor(fiatPrice * teoDiscount / 100)}
          >
            {loading ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Applicando sconto...
              </>
            ) : (
              `🪙 Applica sconto con ${Math.floor(fiatPrice * teoDiscount / 100)} TEO`
            )}
          </Button>
          <small className="text-muted text-center mt-2">
            Dopo lo sconto, completerai il pagamento con carta per €{(fiatPrice - fiatPrice * teoDiscount / 100).toFixed(2)}
          </small>
        </div>
      </div>
    );
  };

  return (
    <Modal show={show} onHide={handleClose} size="lg" centered>
      <Modal.Header closeButton>
        <Modal.Title>
          💳 Acquista Corso: {course?.title}
        </Modal.Title>
      </Modal.Header>
      
      <Modal.Body>
        <Tab.Container activeKey={activeTab} onSelect={setActiveTab}>
          <Nav variant="pills" className="justify-content-center mb-4">
            <Nav.Item>
              <Nav.Link eventKey="fiat" className="mx-2">
                💳 Carta di Credito
              </Nav.Link>
            </Nav.Item>
            <Nav.Item>
              <Nav.Link eventKey="teocoin" className="mx-2">
                🪙 Sconto TeoCoin
              </Nav.Link>
            </Nav.Item>
          </Nav>

          <Tab.Content>
            <Tab.Pane eventKey="fiat">
              {renderFiatPaymentTab()}
            </Tab.Pane>
            
            <Tab.Pane eventKey="teocoin">
              {renderTeoCoinPaymentTab()}
            </Tab.Pane>
          </Tab.Content>
        </Tab.Container>
      </Modal.Body>
      
      {step === 'confirm' && (
        <Modal.Footer>
          <Button variant="secondary" onClick={handleClose}>
            Annulla
          </Button>
        </Modal.Footer>
      )}
    </Modal>
  );
};

export default CourseCheckoutModal;
