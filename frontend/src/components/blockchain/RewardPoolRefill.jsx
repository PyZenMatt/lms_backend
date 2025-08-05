import React, { useState } from 'react';
import { Card, Form, Button, InputGroup, Alert, Spinner } from 'react-bootstrap';
import { refillRewardPool } from '../../services/api/blockchain';
import './RewardPoolRefill.scss';

/**
 * Component for admin to refill the reward pool with MATIC
 */
const RewardPoolRefill = ({ onRefillComplete }) => {
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleAmountChange = (e) => {
    const value = e.target.value;
    // Only allow numbers and decimals
    if (value === '' || /^\d*\.?\d*$/.test(value)) {
      setAmount(value);
    }
  };

  const handleRefill = async (e) => {
    e.preventDefault();
    
    if (!amount || parseFloat(amount) <= 0) {
      setError('Please enter a valid amount greater than 0');
      return;
    }
    
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      const response = await refillRewardPool(amount);
      setSuccess(`Successfully transferred ${amount} MATIC to reward pool. Transaction hash: ${response.data.tx_hash}`);
      setAmount('');
      
      // Callback to refresh parent component
      if (onRefillComplete) {
        onRefillComplete();
      }
    } catch (err) {
      console.error('Error refilling reward pool:', err);
      setError(err.response?.data?.error || 'Error refilling reward pool. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="reward-pool-refill">
      <Card.Header>
        <Card.Title as="h5">
          <i className="feather icon-plus-circle mr-2"></i>
          Refill Reward Pool
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
        
        <Form onSubmit={handleRefill}>
          <Form.Group className="mb-3">
            <Form.Label>MATIC Amount</Form.Label>
            <InputGroup>
              <Form.Control
                type="text"
                value={amount}
                onChange={handleAmountChange}
                placeholder="Enter MATIC amount to transfer"
                disabled={loading}
              />
              <InputGroup.Text>MATIC</InputGroup.Text>
            </InputGroup>
            <Form.Text className="text-muted">
              This will transfer MATIC from admin wallet to the reward pool to cover gas fees.
            </Form.Text>
          </Form.Group>
          
          <Button
            variant="primary"
            type="submit"
            disabled={loading || !amount}
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
                Transfer MATIC to Reward Pool
              </>
            )}
          </Button>
        </Form>
      </Card.Body>
    </Card>
  );
};

export default RewardPoolRefill;
