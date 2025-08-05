import React, { useState } from 'react';
import { Card, Form, Button, InputGroup, Alert, Spinner } from 'react-bootstrap';
import { refillRewardPool } from '../../services/api/blockchain';
import './RewardPoolRefill.scss';

/**
    const [success, setSuccess] = useState(''); // This line is kept for context
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
    return null;
            )}
          </Button>
        </Form>
      </Card.Body>
    </Card>
  );
};

export default RewardPoolRefill;
