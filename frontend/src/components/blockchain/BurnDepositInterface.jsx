/**
 * TeoCoin Burn Deposit Component
 * Allows users to burn TEO tokens from MetaMask and credit platform balance
 */
import React, { useState, useEffect } from 'react';
import { Card, Spinner, Button, Modal, Form, Alert } from 'react-bootstrap';
import { useAuth } from '../../contexts/AuthContext';
import { ethers } from 'ethers';

const BurnDepositInterface = ({ onTransactionComplete }) => {
  const { user: currentUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [burnAmount, setBurnAmount] = useState('');
  const [metamaskBalance, setMetamaskBalance] = useState('0');
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [lastTxHash, setLastTxHash] = useState('');
  
  // MetaMask connection
  const [isConnected, setIsConnected] = useState(false);
  const [account, setAccount] = useState('');

  // Check MetaMask connection
  useEffect(() => {
    checkMetaMaskConnection();
  }, []);

  const checkMetaMaskConnection = async () => {
    if (typeof window.ethereum !== 'undefined') {
      try {
        const accounts = await window.ethereum.request({ method: 'eth_accounts' });
        if (accounts.length > 0) {
          setAccount(accounts[0]);
          setIsConnected(true);
          await loadMetaMaskBalance(accounts[0]);
        }
      } catch (error) {
        console.error('Error checking MetaMask connection:', error);
      }
    }
  };

  const connectMetaMask = async () => {
    if (typeof window.ethereum === 'undefined') {
      setError('MetaMask is not installed. Please install MetaMask to use this feature.');
      return;
    }

    try {
      const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
      if (accounts.length > 0) {
        setAccount(accounts[0]);
        setIsConnected(true);
        await loadMetaMaskBalance(accounts[0]);
        setError('');
      }
    } catch (error) {
      setError('Failed to connect to MetaMask: ' + error.message);
    }
  };

  const loadMetaMaskBalance = async (userAccount) => {
    try {
      if (!window.ethereum) return;

      const provider = new ethers.BrowserProvider(window.ethereum);
      
      // TeoCoin contract configuration
      const TEO_CONTRACT_ADDRESS = '0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8';
      const TEO_ABI = [
        {
          "constant": true,
          "inputs": [{"name": "_owner", "type": "address"}],
          "name": "balanceOf",
          "outputs": [{"name": "balance", "type": "uint256"}],
          "type": "function"
        },
        {
          "constant": false,
          "inputs": [{"name": "_value", "type": "uint256"}],
          "name": "burn",
          "outputs": [],
          "type": "function"
        }
      ];

      const contract = new ethers.Contract(TEO_CONTRACT_ADDRESS, TEO_ABI, provider);
      const balance = await contract.balanceOf(userAccount);
      const balanceInTEO = ethers.formatEther(balance);
      
      setMetamaskBalance(parseFloat(balanceInTEO).toFixed(6));
    } catch (error) {
      console.error('Error loading MetaMask balance:', error);
      setMetamaskBalance('Error');
    }
  };

  const handleBurnDeposit = async () => {
    if (!burnAmount || parseFloat(burnAmount) <= 0) {
      setError('Please enter a valid amount to burn');
      return;
    }

    if (parseFloat(burnAmount) > parseFloat(metamaskBalance)) {
      setError('Insufficient TEO balance in MetaMask');
      return;
    }

    setProcessing(true);
    setError('');
    setSuccess('');

    try {
      const provider = new ethers.BrowserProvider(window.ethereum);
      const signer = await provider.getSigner();
      
      // Contract setup
      const TEO_CONTRACT_ADDRESS = '0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8';
      const TEO_ABI = [
        {
          "constant": false,
          "inputs": [{"name": "_value", "type": "uint256"}],
          "name": "burn",
          "outputs": [],
          "type": "function"
        }
      ];

      const contract = new ethers.Contract(TEO_CONTRACT_ADDRESS, TEO_ABI, signer);
      const amountWei = ethers.parseEther(burnAmount);

      // Step 1: Execute burn transaction in MetaMask
      const burnTx = await contract.burn(amountWei);
      const burnResult = await burnTx.wait();

      const txHash = burnResult.hash || burnTx.hash;
      setLastTxHash(txHash);

      // Step 2: Submit burn proof to backend
      const response = await fetch('/api/v1/teocoin/burn-deposit/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          transaction_hash: txHash,
          amount: burnAmount,
          metamask_address: account
        })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setSuccess(`🎉 Successfully deposited ${burnAmount} TEO to your platform balance! TX: ${txHash.substring(0, 10)}...`);
        setBurnAmount('');
        setShowModal(false);
        
        // Refresh MetaMask balance
        await loadMetaMaskBalance(account);
        
        // Trigger parent component refresh
        if (onTransactionComplete) {
          onTransactionComplete(data);
        }
        
        // Also trigger event for other listeners
        window.dispatchEvent(new Event('teocoin-balance-updated'));
      } else {
        throw new Error(data.error || 'Failed to process burn deposit');
      }

    } catch (error) {
      console.error('Burn deposit error:', error);
      setError(`Failed to process burn deposit: ${error.message}`);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <>
      <Card className="border-0 shadow-sm">
        <Card.Header className="bg-gradient-primary text-white">
          <h5 className="mb-0">
            <i className="fas fa-fire me-2"></i>
            Deposit TEO from MetaMask
          </h5>
        </Card.Header>
        <Card.Body>
          {!isConnected ? (
            <div className="text-center py-3">
              <i className="fab fa-ethereum fa-3x text-primary mb-3"></i>
              <p className="text-muted mb-3">Connect your MetaMask wallet to deposit TEO tokens</p>
              
              {/* Debug Info */}
              <div className="alert alert-info small text-start mb-3">
                <strong>Debug Info:</strong><br/>
                MetaMask Available: {typeof window.ethereum !== 'undefined' ? 'Yes' : 'No'}<br/>
                Current Status: Not Connected
              </div>
              
              <Button 
                variant="primary" 
                onClick={connectMetaMask}
                style={{ 
                  backgroundColor: '#007bff', 
                  borderColor: '#007bff', 
                  color: 'white',
                  fontWeight: 'bold'
                }}
              >
                <i className="fas fa-wallet me-2"></i>
                Connect MetaMask
              </Button>
            </div>
          ) : (
            <div>
              {/* Debug Info for Connected State */}
              <div className="alert alert-info small mb-3">
                <strong>Debug Info:</strong><br/>
                Connected: Yes<br/>
                Account: {account}<br/>
                Balance: {metamaskBalance} TEO<br/>
                {error && <><span className="text-danger">Error: {error}</span><br/></>}
                {success && <><span className="text-success">Success: {success}</span><br/></>}
              </div>
              
              <div className="d-flex justify-content-between align-items-center mb-3">
                <div>
                  <strong>MetaMask Balance:</strong>
                  <div className="h4 text-primary mb-0">{metamaskBalance} TEO</div>
                </div>
                <div className="text-end">
                  <small className="text-muted">Connected:</small>
                  <div className="small text-success">
                    {account.substring(0, 6)}...{account.substring(account.length - 4)}
                  </div>
                </div>
              </div>

              {error && (
                <Alert variant="danger" dismissible onClose={() => setError('')}>
                  {error}
                </Alert>
              )}

              {success && (
                <Alert variant="success" dismissible onClose={() => setSuccess('')}>
                  {success}
                </Alert>
              )}

              <div className="d-grid gap-2">
                <Button
                  variant="success"
                  onClick={() => {
                    console.log('🔥 Burn & Deposit button clicked');
                    setShowModal(true);
                  }}
                  disabled={parseFloat(metamaskBalance) <= 0}
                  className="btn-success"
                  style={{ 
                    backgroundColor: '#28a745', 
                    borderColor: '#28a745', 
                    color: 'white',
                    fontWeight: 'bold'
                  }}
                >
                  <i className="fas fa-fire me-2"></i>
                  Burn & Deposit TEO
                </Button>
                
                <Button
                  variant="outline-primary"
                  size="sm"
                  onClick={() => {
                    console.log('🔄 Refresh button clicked');
                    loadMetaMaskBalance(account);
                  }}
                  disabled={loading}
                  className="btn-outline-primary"
                  style={{ 
                    borderColor: '#007bff', 
                    color: '#007bff',
                    fontWeight: '500'
                  }}
                >
                  <i className="fas fa-sync-alt me-1"></i>
                  Refresh Balance
                </Button>
              </div>

              <div className="mt-3 small text-muted">
                <div className="d-flex justify-content-between">
                  <span>Process:</span>
                  <span>Burn → Credit Platform</span>
                </div>
                <div className="d-flex justify-content-between">
                  <span>Network:</span>
                  <span>Polygon Amoy</span>
                </div>
              </div>
            </div>
          )}
        </Card.Body>
      </Card>

      {/* Burn Deposit Modal */}
      <Modal show={showModal} onHide={() => setShowModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>
            <i className="fas fa-fire text-danger me-2"></i>
            Burn & Deposit TEO
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="alert alert-warning">
            <i className="fas fa-exclamation-triangle me-2"></i>
            <strong>Warning:</strong> Burning tokens is permanent! TEO will be removed from your MetaMask and added to your platform balance.
          </div>

          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Amount to Burn & Deposit</Form.Label>
              <Form.Control
                type="number"
                step="0.01"
                min="0"
                max={metamaskBalance}
                value={burnAmount}
                onChange={(e) => setBurnAmount(e.target.value)}
                placeholder="Enter amount to burn"
                disabled={processing}
              />
              <Form.Text className="text-muted">
                Available in MetaMask: {metamaskBalance} TEO
              </Form.Text>
            </Form.Group>

            <div className="bg-light p-3 rounded mb-3">
              <h6>Transaction Summary:</h6>
              <div className="d-flex justify-content-between">
                <span>From MetaMask:</span>
                <span className="text-danger">-{burnAmount || '0'} TEO</span>
              </div>
              <div className="d-flex justify-content-between">
                <span>To Platform:</span>
                <span className="text-success">+{burnAmount || '0'} TEO</span>
              </div>
            </div>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModal(false)} disabled={processing}>
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={handleBurnDeposit}
            disabled={processing || !burnAmount || parseFloat(burnAmount) <= 0}
          >
            {processing ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Processing...
              </>
            ) : (
              <>
                <i className="fas fa-fire me-2"></i>
                Burn & Deposit
              </>
            )}
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
};

export default BurnDepositInterface;
