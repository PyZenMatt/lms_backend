import React, { useState, useEffect } from 'react';
import { Toast, ToastContainer, Badge } from 'react-bootstrap';
import { useAuth } from '../../contexts/AuthContext';
import { blockchainAPI } from '../../services/api/blockchainAPI';
import './RewardNotification.scss';

const RewardNotification = () => {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [lastTransactionId, setLastTransactionId] = useState(null);

  useEffect(() => {
    if (!user?.wallet_address) return;

    // Check for new rewards every 10 seconds
    const interval = setInterval(checkForNewRewards, 10000);
    
    // Initial check
    checkForNewRewards();

    return () => clearInterval(interval);
  }, [user?.wallet_address]);

  const checkForNewRewards = async () => {
    try {
      const response = await blockchainAPI.getTransactionHistory();
      const transactions = response.transactions || [];
      
      // Filter for reward transactions
      const rewardTransactions = transactions.filter(tx => 
        tx.transaction_type && 
        ['earned', 'exercise_reward', 'review_reward', 'achievement_reward', 'bonus', 'mint'].includes(tx.transaction_type) &&
        parseFloat(tx.amount) > 0
      );

      if (rewardTransactions.length > 0) {
        const latestTransaction = rewardTransactions[0];
        
        // Show notification only for new transactions
        if (lastTransactionId !== latestTransaction.id) {
          showRewardNotification(latestTransaction);
          setLastTransactionId(latestTransaction.id);
        }
      }
    } catch (error) {
      console.error('Error checking for new rewards:', error);
    }
  };

  const showRewardNotification = (transaction) => {
    const notification = {
      id: Date.now(),
      transaction,
      show: true,
      timestamp: new Date()
    };

    setNotifications(prev => [notification, ...prev.slice(0, 2)]); // Keep max 3 notifications

    // Auto-hide after 8 seconds
    setTimeout(() => {
      hideNotification(notification.id);
    }, 8000);
  };

  const hideNotification = (id) => {
    setNotifications(prev => 
      prev.map(notif => 
        notif.id === id ? { ...notif, show: false } : notif
      )
    );

    // Remove from state after animation
    setTimeout(() => {
      setNotifications(prev => prev.filter(notif => notif.id !== id));
    }, 300);
  };

  const getRewardIcon = (transactionType) => {
    const iconMap = {
      'earned': '💰',
      'exercise_reward': '🎉',
      'review_reward': '⭐',
      'achievement_reward': '🏆',
      'bonus': '🎁',
      'mint': '🪙'
    };
    return iconMap[transactionType] || '💰';
  };

  const getRewardMessage = (transaction) => {
    const { transaction_type, amount } = transaction;
    const formattedAmount = parseFloat(amount).toFixed(2);

    const messageMap = {
      'earned': `Hai guadagnato ${formattedAmount} TEO!`,
      'exercise_reward': `Esercizio valutato! +${formattedAmount} TEO`,
      'review_reward': `Review completata! +${formattedAmount} TEO`,
      'achievement_reward': `Achievement sbloccato! +${formattedAmount} TEO`,
      'bonus': `Bonus ricevuto! +${formattedAmount} TEO`,
      'mint': `TeoCoins ricevuti! +${formattedAmount} TEO`
    };

    return messageMap[transaction_type] || `Ricompensa ricevuta! +${formattedAmount} TEO`;
  };

  const getTransactionDetails = (transaction) => {
    if (transaction.tx_hash) {
      return {
        hash: transaction.tx_hash,
        shortHash: `${transaction.tx_hash.substring(0, 8)}...${transaction.tx_hash.substring(transaction.tx_hash.length - 6)}`,
        explorerUrl: `https://amoy.polygonscan.com/tx/${transaction.tx_hash}`
      };
    }
    return null;
  };

  return (
    <ToastContainer position="top-end" className="reward-notification-container">
      {notifications.map((notification) => {
        const details = getTransactionDetails(notification.transaction);
        
        return (
          <Toast 
            key={notification.id} 
            show={notification.show} 
            onClose={() => hideNotification(notification.id)}
            className="reward-toast"
            delay={8000}
            autohide
          >
            <Toast.Header className="reward-toast-header">
              <div className="reward-icon me-2">
                {getRewardIcon(notification.transaction.transaction_type)}
              </div>
              <strong className="me-auto text-success">TeoCoins Ricevuti!</strong>
              <Badge bg="success" className="ms-2">
                +{parseFloat(notification.transaction.amount).toFixed(2)} TEO
              </Badge>
            </Toast.Header>
            <Toast.Body className="reward-toast-body">
              <div className="reward-message mb-2">
                {getRewardMessage(notification.transaction)}
              </div>
              
              {details && (
                <div className="transaction-details">
                  <small className="text-muted d-flex justify-content-between align-items-center">
                    <span>TX: {details.shortHash}</span>
                    <a 
                      href={details.explorerUrl} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-primary"
                      style={{ fontSize: '12px' }}
                    >
                      <i className="feather icon-external-link me-1"></i>
                      Visualizza
                    </a>
                  </small>
                </div>
              )}
              
              <div className="timestamp mt-1">
                <small className="text-muted">
                  {notification.timestamp.toLocaleTimeString()}
                </small>
              </div>
            </Toast.Body>
          </Toast>
        );
      })}
    </ToastContainer>
  );
};

export default RewardNotification;
