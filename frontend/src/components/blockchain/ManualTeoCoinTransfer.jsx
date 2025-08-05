import React, { useState } from 'react';
import { Card, Form, Button, InputGroup, Alert, Spinner } from 'react-bootstrap';
import { manualTeoCoinTransfer } from '../../services/api/blockchain';
import './ManualTeoCoinTransfer.scss';

/**
 * Component for admin to manually transfer TeoCoins to users
 */
const ManualTeoCoinTransfer = ({ onTransferComplete }) => {
  const [formData, setFormData] = useState({
    toAddress: '',
    amount: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    
    if (name === 'amount' && value !== '') {
      // Only allow numbers and decimals for amount
      if (!/^\d*\.?\d*$/.test(value)) return;
    }
    
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const validateForm = () => {
    if (!formData.toAddress) {
      setError('Wallet address is required');
      return false;
    }
    
    if (!formData.amount || parseFloat(formData.amount) <= 0) {
      setError('Please enter a valid amount greater than 0');
      return false;
    }
    
    return true;
  };

  const handleTransfer = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      const response = await manualTeoCoinTransfer({
        toAddress: formData.toAddress,
        amount: formData.amount
      });
      
      setSuccess(`Successfully transferred ${formData.amount} TEO to ${formData.toAddress}. Transaction hash: ${response.data.tx_hash}`);
      setFormData({
        toAddress: '',
        amount: ''
      });
      
      // Callback to refresh parent component
      if (onTransferComplete) {
        onTransferComplete();
      }
    } catch (err) {
      console.error('Error transferring TeoCoins:', err);
      setError(err.response?.data?.error || 'Error transferring TeoCoins. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="manual-teocoin-transfer">
      <Card.Header>
        <Card.Title as="h5">
          <i className="feather icon-send mr-2"></i>
          Manual TeoCoin Transfer
        </Card.Title>
      </Card.Header>
      <Card.Body>
        {error && (
          <Alert variant="danger" onClose={() => setError('')} dismissible>
            <i className="feather icon-alert-circle mr-2"></i>
            {error}
          </Alert>
        )}
        
        {success && (
          <Alert variant="success" onClose={() => setSuccess('')} dismissible>
            <i className="feather icon-check-circle mr-2"></i>
            {success}
          </Alert>
        )}
        
        <Form onSubmit={handleTransfer}>
          <Form.Group className="mb-3">
            <Form.Label>Recipient Wallet Address</Form.Label>
            <Form.Control
              type="text"
              name="toAddress"
              value={formData.toAddress}
              onChange={handleInputChange}
              placeholder="0x..."
              disabled={loading}
            />
            <Form.Text className="text-muted">
              Enter the Ethereum wallet address of the recipient
            </Form.Text>
          </Form.Group>
          
          <Form.Group className="mb-3">
            <Form.Label>TeoCoin Amount</Form.Label>
            <InputGroup>
              <Form.Control
                type="text"
                name="amount"
                value={formData.amount}
                onChange={handleInputChange}
                placeholder="Enter TeoCoin amount"
                disabled={loading}
              />
              <InputGroup.Text>TEO</InputGroup.Text>
            </InputGroup>
          </Form.Group>
          
          <Button
            variant="primary"
            type="submit"
            disabled={loading || !formData.toAddress || !formData.amount}
            className="w-100"
          >
            {loading ? (
              <>
                <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" className="mr-2" />
                Processing...
              </>
            ) : (
              <>
                <i className="feather icon-send mr-2"></i>
                Transfer TeoCoins
              </>
            )}
          </Button>
        </Form>
      </Card.Body>
    </Card>
  );
};

export default ManualTeoCoinTransfer;
