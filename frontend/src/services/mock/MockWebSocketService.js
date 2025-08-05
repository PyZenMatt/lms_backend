/**
 * 🔧 Mock WebSocket Service
 * 
 * Provides mock WebSocket functionality when backend is not available
 */

class MockWebSocketService {
  constructor() {
    this.isConnected = false;
    this.listeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.messageQueue = [];
    this.simulationInterval = null;
    
    // Event types (same as real WebSocket service)
    this.events = {
      NEW_NOTIFICATION: 'new_notification',
      TEOCOIN_TRANSACTION: 'teocoin_transaction',
      COURSE_UPDATE: 'course_update',
      DISCOUNT_REQUEST: 'discount_request',
      USER_ACTIVITY: 'user_activity',
      COURSE_PROGRESS: 'course_progress',
      PEER_REVIEW_REQUEST: 'peer_review_request',
      ACHIEVEMENT_UNLOCKED: 'achievement_unlocked',
      CONNECTION_STATUS: 'connection_status'
    };
  }

  /**
   * Mock connection (always succeeds in development)
   */
  connect(token) {
    console.log('🔌 Mock WebSocket: Simulating connection...');
    
    setTimeout(() => {
      this.isConnected = true;
      this.reconnectAttempts = 0;
      
      // Emit connection success
      this.emit(this.events.CONNECTION_STATUS, {
        status: 'connected',
        message: 'Mock WebSocket connected successfully'
      });
      
      console.log('✅ Mock WebSocket: Connected successfully');
      
      // Start simulation
      this.startSimulation();
      
    }, 1000);
  }

  /**
   * Start simulating real-time events
   */
  startSimulation() {
    // Simulate periodic events
    this.simulationInterval = setInterval(() => {
      this.simulateRandomEvent();
    }, 15000); // Every 15 seconds
  }

  /**
   * Simulate random WebSocket events
   */
  simulateRandomEvent() {
    if (!this.isConnected) return;

    const events = [
      {
        type: this.events.NEW_NOTIFICATION,
        data: {
          id: `notif_${Date.now()}`,
          title: 'New Course Available',
          message: 'Check out the latest React Advanced course!',
          type: 'info',
          timestamp: new Date().toISOString()
        }
      },
      {
        type: this.events.TEOCOIN_TRANSACTION,
        data: {
          id: `tx_${Date.now()}`,
          amount: Math.floor(Math.random() * 50) + 10,
          type: 'earned',
          reason: 'Exercise completion',
          timestamp: new Date().toISOString()
        }
      },
      {
        type: this.events.USER_ACTIVITY,
        data: {
          id: `activity_${Date.now()}`,
          user: 'Study Buddy',
          action: 'completed a lesson',
          course: 'JavaScript Fundamentals',
          timestamp: new Date().toISOString()
        }
      },
      {
        type: this.events.ACHIEVEMENT_UNLOCKED,
        data: {
          id: `achievement_${Date.now()}`,
          title: 'Study Streak Champion',
          description: 'Completed lessons for 7 days in a row!',
          points: 100,
          timestamp: new Date().toISOString()
        }
      }
    ];

    const randomEvent = events[Math.floor(Math.random() * events.length)];
    this.emit(randomEvent.type, randomEvent.data);
  }

  /**
   * Subscribe to events
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
    
    console.log(`📡 Mock WebSocket: Subscribed to ${event}`);
  }

  /**
   * Unsubscribe from events
   */
  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  /**
   * Emit events to listeners
   */
  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`❌ Mock WebSocket: Error in ${event} callback:`, error);
        }
      });
    }
  }

  /**
   * Send message (mock implementation)
   */
  send(message) {
    if (!this.isConnected) {
      console.warn('⚠️ Mock WebSocket: Not connected, queueing message');
      this.messageQueue.push(message);
      return;
    }

    console.log('📤 Mock WebSocket: Sending message:', message);
    
    // Simulate echo response for some message types
    setTimeout(() => {
      if (message.type === 'ping') {
        this.emit('pong', { timestamp: Date.now() });
      }
    }, 100);
  }

  /**
   * Disconnect
   */
  disconnect() {
    console.log('🔌 Mock WebSocket: Disconnecting...');
    
    this.isConnected = false;
    
    if (this.simulationInterval) {
      clearInterval(this.simulationInterval);
      this.simulationInterval = null;
    }
    
    this.emit(this.events.CONNECTION_STATUS, {
      status: 'disconnected',
      message: 'Mock WebSocket disconnected'
    });
  }

  /**
   * Check connection status
   */
  isConnectedStatus() {
    return this.isConnected;
  }

  /**
   * Get connection health
   */
  getConnectionHealth() {
    return {
      isConnected: this.isConnected,
      reconnectAttempts: this.reconnectAttempts,
      lastActivity: new Date().toISOString(),
      queuedMessages: this.messageQueue.length,
      mode: 'mock'
    };
  }
}

export default MockWebSocketService;
