import React, { useState, useEffect } from 'react';
import { Toast, ToastContainer } from 'react-bootstrap';
import { blockchainAPI } from '../../services/api/blockchainAPI';
import { useAuth } from '../../contexts/AuthContext';
import './RewardNotifications.scss';

const RewardNotifications = () => {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [lastCheckedBalance, setLastCheckedBalance] = useState(0);

  // Check for new rewards every 30 seconds
  useEffect(() => {
    const checkForNewRewards = async () => {
      try {
        // Temporaneamente disabilitato - la funzione getWalletBalance non esiste
        console.log('🔍 Check rewards temporaneamente disabilitato');
        return;
        
        // TODO: Implementare controllo rewards corretto
        // const response = await blockchainAPI.getWalletBalance();
        // const currentBalance = parseFloat(response.data?.balance) || 0;
        
        // if (lastCheckedBalance > 0 && currentBalance > lastCheckedBalance) {
        //   const rewardAmount = currentBalance - lastCheckedBalance;
        //   addRewardNotification(rewardAmount);
        // }
        
        // setLastCheckedBalance(currentBalance);
      } catch (error) {
        console.error('Error checking for new rewards:', error);
      }
    };

    // Initial check
    checkForNewRewards();
    
    // Set up interval
    const interval = setInterval(checkForNewRewards, 30000);
    
    return () => clearInterval(interval);
  }, [lastCheckedBalance]);

  const addRewardNotification = (amount) => {
    const notification = {
      id: Date.now(),
      type: 'reward',
      amount: amount,
      timestamp: new Date(),
      show: true
    };
    
    setNotifications(prev => [...prev, notification]);
    
    // Auto-hide after 8 seconds
    setTimeout(() => {
      removeNotification(notification.id);
    }, 8000);
  };

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(notif => notif.id !== id));
  };

  const formatAmount = (amount) => {
    return amount.toFixed(2);
  };

  const getRewardIcon = (type) => {
    switch (type) {
      case 'reward':
        return '🎉';
      case 'achievement':
        return '🏆';
      case 'bonus':
        return '💰';
      default:
        return '✨';
    }
  };

  return (
    <ToastContainer className="reward-notifications" position="top-end">
      {notifications.map((notification) => (
        <Toast
          key={notification.id}
          show={notification.show}
          onClose={() => removeNotification(notification.id)}
          className="reward-toast"
          autohide={false}
        >
          <Toast.Header className="reward-toast-header">
            <div className="reward-icon me-2">
              {getRewardIcon(notification.type)}
            </div>
            <strong className="me-auto">Nuovo Reward!</strong>
            <small className="text-muted">
              {notification.timestamp.toLocaleTimeString('it-IT', {
                hour: '2-digit',
                minute: '2-digit'
              })}
            </small>
          </Toast.Header>
          <Toast.Body className="reward-toast-body">
            <div className="reward-content">
              <div className="reward-message">
                Hai ricevuto <strong>{formatAmount(notification.amount)} TEO</strong> coins!
              </div>
              <div className="reward-details">
                <small className="text-muted">
                  <i className="feather icon-trending-up me-1"></i>
                  Aggiunto al tuo wallet
                </small>
              </div>
            </div>
          </Toast.Body>
        </Toast>
      ))}
    </ToastContainer>
  );
};

export default RewardNotifications;
