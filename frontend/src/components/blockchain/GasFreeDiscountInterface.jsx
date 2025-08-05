/**
 * Gas-Free Discount Interface
 * Allows students to request discounts without MATIC gas fees
 */
import React, { useState, useEffect } from 'react';
import { Card, Button, Alert, Form, Badge, Spinner } from 'react-bootstrap';
import { ethers } from 'ethers';
import './GasFreeDiscountInterface.scss';

const GasFreeDiscountInterface = ({ 
  course, 
  userAddress, 
  onDiscountRequested,
  className = ""
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [teoAmount, setTeoAmount] = useState(100);
  const [gasCostEstimate, setGasCostEstimate] = useState(null);
  const [signatureData, setSignatureData] = useState(null);
  const [walletConnected, setWalletConnected] = useState(false);

  // Check wallet connection on component mount
  useEffect(() => {
    checkWalletConnection();
    fetchGasCostEstimate();
  }, []);

  const checkWalletConnection = async () => {
    try {
      if (window.ethereum && userAddress) {
        setWalletConnected(true);
      }
    } catch (error) {
      console.error('Error checking wallet connection:', error);
    }
  };

  const fetchGasCostEstimate = async () => {
    try {
      const response = await fetch('/api/v1/services/gas-free/gas-estimates/', {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setGasCostEstimate(data.data.discount_operations);
      }
    } catch (error) {
      console.error('Error fetching gas estimates:', error);
    }
  };

  const createDiscountSignature = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Step 1: Request signature data from backend
      const response = await fetch('/api/v1/services/gas-free/discount/signature/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          student_address: userAddress,
          course_id: course.id,
          teo_amount: teoAmount
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to create signature data');
      }

      const signatureResponse = await response.json();
      const signatureInfo = signatureResponse.data;
      
      setSignatureData(signatureInfo);
      
      // Step 2: Request user to sign the message
      await requestUserSignature(signatureInfo);
      
    } catch (error) {
      console.error('Error creating discount signature:', error);
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const requestUserSignature = async (signatureInfo) => {
    try {
      if (!window.ethereum) {
        throw new Error('MetaMask not found. Please install MetaMask.');
      }

      const provider = new ethers.BrowserProvider(window.ethereum);
      const signer = await provider.getSigner();
      
      // Create the message to sign
      const messageToSign = signatureInfo.message_hash;
      
      // Request signature from user
      const signature = await signer.signMessage(ethers.getBytes(messageToSign));
      
      // Step 3: Execute the discount request
      await executeDiscountRequest(signatureInfo, signature);
      
    } catch (error) {
      if (error.code === 4001) {
        setError('Transaction cancelled by user');
      } else {
        console.error('Error requesting signature:', error);
        setError('Failed to sign message: ' + error.message);
      }
    }
  };

  const executeDiscountRequest = async (signatureInfo, signature) => {
    try {
      const response = await fetch('/api/v1/services/gas-free/discount/execute/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          student_address: signatureInfo.student_address,
          signature: signature,
          course_id: signatureInfo.course_id,
          teo_amount: signatureInfo.teo_amount,
          nonce: signatureInfo.nonce
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to execute discount request');
      }

      const result = await response.json();
      
      // Handle response structure - V2 API returns data directly
      const responseData = result.data || result; // Fallback for different response structures
      
      setSuccess({
        message: 'Discount request submitted successfully!',
        transactionHash: responseData.transaction_hash || result.transaction_hash || 'processing',
        requestId: responseData.discount_request_id || result.discount_request_id || result.request_id,
        gasCost: responseData.gas_cost || result.gas_cost || '0.00'
      });
      
      // Notify parent component
      if (onDiscountRequested) {
        onDiscountRequested(responseData.transaction_hash ? responseData : result);
      }
      
    } catch (error) {
      console.error('Error executing discount request:', error);
      setError('Failed to execute discount request: ' + error.message);
    }
  };

  const formatGasCost = (costInWei) => {
    if (!costInWei) return 'N/A';
    const costInEther = ethers.formatEther(costInWei.toString());
    const costInUSD = parseFloat(costInEther) * 0.5; // Approximate MATIC to USD
    return `$${costInUSD.toFixed(4)} USD`;
  };

  return (
    <Card className={`gas-free-discount-interface ${className}`}>
      <Card.Header className="bg-primary text-white">
        <div className="d-flex justify-content-between align-items-center">
          <h5 className="mb-0">
            <i className="fas fa-gas-pump me-2"></i>
            Gas-Free Discount Request
          </h5>
          <Badge bg="success">No MATIC Required</Badge>
        </div>
      </Card.Header>
      
      <Card.Body>
        {/* Course Information */}
        <div className="course-info mb-3">
          <h6 className="text-muted">Course: {course?.title || 'Unknown Course'}</h6>
          <p className="small text-muted mb-0">
            Request a discount using TEO tokens. Platform pays all gas fees!
          </p>
        </div>

        {/* TEO Amount Input */}
        <Form.Group className="mb-3">
          <Form.Label>TEO Token Amount</Form.Label>
          <div className="input-group">
            <Form.Control
              type="number"
              value={teoAmount}
              onChange={(e) => setTeoAmount(parseInt(e.target.value) || 0)}
              min="1"
              max="1000"
              disabled={isLoading}
            />
            <span className="input-group-text">TEO</span>
          </div>
          <Form.Text className="text-muted">
            Amount of TEO tokens to spend for discount
          </Form.Text>
        </Form.Group>

        {/* Gas Cost Information */}
        {gasCostEstimate && (
          <Alert variant="info" className="mb-3">
            <div className="d-flex justify-content-between align-items-center">
              <span>
                <i className="fas fa-info-circle me-2"></i>
                Estimated Platform Gas Cost:
              </span>
              <Badge bg="info">
                ${gasCostEstimate.discount_request?.cost_usd?.toFixed(4) || '0.002'} USD
              </Badge>
            </div>
            <small className="text-muted d-block mt-1">
              This cost is paid by the platform, not you!
            </small>
          </Alert>
        )}

        {/* Wallet Connection Status */}
        {!walletConnected && (
          <Alert variant="warning" className="mb-3">
            <i className="fas fa-wallet me-2"></i>
            Please connect your wallet to continue
          </Alert>
        )}

        {/* Error Display */}
        {error && (
          <Alert variant="danger" className="mb-3">
            <i className="fas fa-exclamation-triangle me-2"></i>
            {error}
          </Alert>
        )}

        {/* Success Display */}
        {success && (
          <Alert variant="success" className="mb-3">
            <div className="d-flex flex-column">
              <div>
                <i className="fas fa-check-circle me-2"></i>
                {success.message}
              </div>
              {success.requestId && (
                <small className="text-muted mt-1">
                  Request ID: {success.requestId}
                </small>
              )}
              {success.transactionHash && (
                <small className="text-muted">
                  <a 
                    href={`https://amoy.polygonscan.com/tx/${success.transactionHash}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-decoration-none"
                  >
                    View on PolygonScan <i className="fas fa-external-link-alt"></i>
                  </a>
                </small>
              )}
              {success.gasCost && (
                <small className="text-muted">
                  Platform Gas Cost: {formatGasCost(success.gasCost)}
                </small>
              )}
            </div>
          </Alert>
        )}

        {/* Action Button */}
        <div className="d-grid">
          <Button
            variant="primary"
            size="lg"
            onClick={createDiscountSignature}
            disabled={isLoading || !walletConnected || !teoAmount}
            className="gas-free-btn"
          >
            {isLoading ? (
              <>
                <Spinner
                  as="span"
                  animation="border"
                  size="sm"
                  role="status"
                  aria-hidden="true"
                  className="me-2"
                />
                Processing...
              </>
            ) : (
              <>
                <i className="fas fa-signature me-2"></i>
                Request Gas-Free Discount
              </>
            )}
          </Button>
        </div>

        {/* Process Steps */}
        <div className="process-steps mt-3">
          <small className="text-muted">
            <strong>Process:</strong>
            <ol className="small mt-1 ps-3">
              <li>Sign message with your wallet (no gas required)</li>
              <li>Platform submits transaction and pays gas fees</li>
              <li>Teacher receives notification for approval</li>
              <li>You get discount when approved</li>
            </ol>
          </small>
        </div>
      </Card.Body>
    </Card>
  );
};

export default GasFreeDiscountInterface;
