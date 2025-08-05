/**
 * 🔥 PHASE 4: WebSocket Service for Real-time Features
 * 
 * Provides real-time communication for:
 * - Live notifications (TeoCoin transactions, course updates)
 * - Real-time activity feed
 * - Instant messaging between teachers/students
 * - Live course progress updates
 */

class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000;
    this.listeners = new Map();
    this.isConnected = false;
    this.heartbeatInterval = null;
    this.messageQueue = [];
    
    // Event types
    this.events = {
      // Notification events
      NEW_NOTIFICATION: 'new_notification',
      TEOCOIN_TRANSACTION: 'teocoin_transaction',
      COURSE_UPDATE: 'course_update',
      DISCOUNT_REQUEST: 'discount_request',
      
      // Activity feed events
      USER_ACTIVITY: 'user_activity',
      COURSE_PROGRESS: 'course_progress',
      ACHIEVEMENT_UNLOCKED: 'achievement_unlocked',
      
      // System events
      CONNECTION_STATUS: 'connection_status',
      HEARTBEAT: 'heartbeat',
      USER_ONLINE: 'user_online',
      USER_OFFLINE: 'user_offline'
    };
  }

  /**
   * Initialize WebSocket connection
   */
  connect(token) {
    try {
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = window.location.host;
      const wsUrl = `${wsProtocol}//${wsHost}/ws/notifications/?token=${token}`;
      
      console.log('🔌 Attempting WebSocket connection (will fallback to mock if backend unavailable):', wsUrl);
      
      this.ws = new WebSocket(wsUrl);
      this.setupEventListeners();
      
    } catch (error) {
      console.log('📡 WebSocket unavailable, using mock data for development:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * Setup WebSocket event listeners
   */
  setupEventListeners() {
    this.ws.onopen = () => {
      console.log('✅ WebSocket connected');
      this.isConnected = true;
      this.reconnectAttempts = 0;
      this.startHeartbeat();
      this.flushMessageQueue();
      this.emit(this.events.CONNECTION_STATUS, { connected: true });
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (error) {
        console.error('❌ WebSocket message parsing error:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.log('📡 WebSocket connection unavailable (expected in development):', error);
      this.emit(this.events.CONNECTION_STATUS, { 
        connected: false, 
        error: 'Backend not available - using mock data',
        fallback: 'Demo mode active with sample data'
      });
    };

    this.ws.onclose = (event) => {
      console.log('🔌 WebSocket disconnected:', event.code, event.reason);
      this.isConnected = false;
      this.stopHeartbeat();
      
      this.emit(this.events.CONNECTION_STATUS, { 
        connected: false,
        reason: event.reason || 'Connection closed',
        fallback: 'Switching to demo mode'
      });
      
      // Only attempt reconnection if it wasn't a clean close
      if (event.code !== 1000) {
        this.scheduleReconnect();
      }
    };
  }

  /**
   * Handle incoming WebSocket messages
   */
  handleMessage(data) {
    const { type, payload, timestamp } = data;
    
    switch (type) {
      case this.events.NEW_NOTIFICATION:
        this.handleNotification(payload);
        break;
        
      case this.events.TEOCOIN_TRANSACTION:
        this.handleTeoCoinTransaction(payload);
        break;
        
      case this.events.COURSE_UPDATE:
        this.handleCourseUpdate(payload);
        break;
        
      case this.events.DISCOUNT_REQUEST:
        this.handleDiscountRequest(payload);
        break;
        
      case this.events.USER_ACTIVITY:
        this.handleUserActivity(payload);
        break;
        
      case this.events.COURSE_PROGRESS:
        this.handleCourseProgress(payload);
        break;
        
      case this.events.ACHIEVEMENT_UNLOCKED:
        this.handleAchievement(payload);
        break;
        
      case this.events.HEARTBEAT:
        // Send heartbeat response
        this.send({ type: 'heartbeat_response', timestamp: Date.now() });
        break;
        
      default:
        console.log('🔔 Unknown message type:', type, payload);
    }
    
    // Emit to registered listeners
    this.emit(type, payload);
  }

  /**
   * Handle notification messages
   */
  handleNotification(payload) {
    const { message, notification_type, priority = 'normal' } = payload;
    
    // Show notification with enhanced features
    this.showEnhancedNotification({
      message,
      type: notification_type,
      priority,
      timestamp: Date.now(),
      actions: payload.actions || []
    });
  }

  /**
   * Handle TeoCoin transaction updates
   */
  handleTeoCoinTransaction(payload) {
    const { transaction_type, amount, status, tx_hash } = payload;
    
    let message = '';
    let type = 'info';
    
    switch (transaction_type) {
      case 'reward':
        message = `🎉 You earned ${amount} TEO!`;
        type = 'success';
        break;
      case 'purchase':
        message = `💰 Course purchase: ${amount} TEO`;
        type = 'info';
        break;
      case 'stake':
        message = `🔒 Staked ${amount} TEO successfully`;
        type = 'success';
        break;
      case 'unstake':
        message = `🔓 Unstaked ${amount} TEO`;
        type = 'info';
        break;
      case 'withdrawal':
        message = `💸 Withdrawal of ${amount} TEO ${status === 'completed' ? 'completed' : 'processing'}`;
        type = status === 'completed' ? 'success' : 'info';
        break;
    }
    
    this.showEnhancedNotification({
      message,
      type,
      priority: 'high',
      sound: true,
      actions: tx_hash ? [{
        label: 'View Transaction',
        action: () => window.open(`https://amoy.polygonscan.com/tx/${tx_hash}`, '_blank')
      }] : []
    });
  }

  /**
   * Handle course update notifications
   */
  handleCourseUpdate(payload) {
    const { course_title, update_type, student_count } = payload;
    
    let message = '';
    switch (update_type) {
      case 'new_student':
        message = `📚 New student enrolled in "${course_title}"`;
        break;
      case 'course_completed':
        message = `🎓 Student completed "${course_title}"`;
        break;
      case 'course_approved':
        message = `✅ Your course "${course_title}" has been approved!`;
        break;
      case 'course_rejected':
        message = `❌ Your course "${course_title}" needs revision`;
        break;
    }
    
    this.showEnhancedNotification({
      message,
      type: update_type.includes('approved') || update_type.includes('completed') ? 'success' : 'info',
      priority: 'normal',
      sound: true
    });
  }

  /**
   * Handle discount request notifications
   */
  handleDiscountRequest(payload) {
    const { student_name, course_title, discount_percent, request_id } = payload;
    
    this.showEnhancedNotification({
      message: `💰 ${student_name} requested ${discount_percent}% discount for "${course_title}"`,
      type: 'warning',
      priority: 'high',
      sound: true,
      vibrate: true,
      actions: [
        {
          label: 'Review Request',
          action: () => this.navigateToDiscountRequests(request_id)
        }
      ]
    });
  }

  /**
   * Handle user activity updates
   */
  handleUserActivity(payload) {
    // Emit for activity feed updates
    this.emit('activity_feed_update', payload);
  }

  /**
   * Handle course progress updates
   */
  handleCourseProgress(payload) {
    const { student_name, course_title, progress_percent } = payload;
    
    if (progress_percent === 100) {
      this.showEnhancedNotification({
        message: `🎉 ${student_name} completed "${course_title}"!`,
        type: 'success',
        priority: 'normal',
        sound: true
      });
    }
  }

  /**
   * Handle achievement unlocked
   */
  handleAchievement(payload) {
    const { achievement_name, achievement_icon, reward_amount } = payload;
    
    this.showEnhancedNotification({
      message: `🏆 Achievement Unlocked: ${achievement_name}! ${reward_amount ? `+${reward_amount} TEO` : ''}`,
      type: 'success',
      priority: 'high',
      sound: true,
      vibrate: true,
      duration: 8000
    });
  }

  /**
   * Show enhanced notification with sound/vibration
   */
  showEnhancedNotification(options) {
    const {
      message,
      type = 'info',
      priority = 'normal',
      sound = false,
      vibrate = false,
      duration = 5000,
      actions = []
    } = options;

    // Play notification sound
    if (sound && this.canPlaySound()) {
      this.playNotificationSound(type);
    }

    // Vibrate device (mobile)
    if (vibrate && navigator.vibrate) {
      navigator.vibrate([200, 100, 200]);
    }

    // Emit to notification system
    this.emit('show_notification', {
      message,
      type,
      priority,
      duration,
      actions,
      timestamp: Date.now()
    });

    // Show browser notification if permission granted
    if (this.canShowBrowserNotification() && priority === 'high') {
      this.showBrowserNotification(message, type);
    }
  }

  /**
   * Check if sound can be played
   */
  canPlaySound() {
    return !document.hidden && 'Audio' in window;
  }

  /**
   * Play notification sound based on type
   */
  playNotificationSound(type) {
    try {
      let soundFile = '';
      switch (type) {
        case 'success':
          soundFile = '/sounds/success.mp3';
          break;
        case 'error':
          soundFile = '/sounds/error.mp3';
          break;
        case 'warning':
          soundFile = '/sounds/warning.mp3';
          break;
        default:
          soundFile = '/sounds/notification.mp3';
      }
      
      const audio = new Audio(soundFile);
      audio.volume = 0.3;
      audio.play().catch(e => console.log('Sound play failed:', e));
    } catch (error) {
      console.log('Sound not available:', error);
    }
  }

  /**
   * Check if browser notifications are available
   */
  canShowBrowserNotification() {
    return 'Notification' in window && Notification.permission === 'granted';
  }

  /**
   * Show browser notification
   */
  showBrowserNotification(message, type) {
    if (!this.canShowBrowserNotification()) return;

    const notification = new Notification('SchoolPlatform', {
      body: message,
      icon: '/favicon.ico',
      badge: '/badge.png',
      tag: 'schoolplatform',
      requireInteraction: type === 'error'
    });

    // Auto-close after 5 seconds
    setTimeout(() => notification.close(), 5000);
  }

  /**
   * Navigate to discount requests
   */
  navigateToDiscountRequests(requestId) {
    // This would trigger navigation in the app
    this.emit('navigate', { path: '/teacher/discount-requests', params: { requestId } });
  }

  /**
   * Send message to server
   */
  send(data) {
    if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      // Queue message for when connection is restored
      this.messageQueue.push(data);
    }
  }

  /**
   * Send queued messages
   */
  flushMessageQueue() {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      this.send(message);
    }
  }

  /**
   * Start heartbeat to keep connection alive
   */
  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected) {
        this.send({ type: 'heartbeat', timestamp: Date.now() });
      }
    }, 30000); // Every 30 seconds
  }

  /**
   * Stop heartbeat
   */
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Schedule reconnection attempt
   */
  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('❌ Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff
    
    console.log(`🔄 Scheduling reconnection attempt ${this.reconnectAttempts} in ${delay}ms`);
    
    setTimeout(() => {
      const token = localStorage.getItem('accessToken');
      if (token) {
        this.connect(token);
      }
    }, delay);
  }

  /**
   * Register event listener
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  /**
   * Remove event listener
   */
  off(event, callback) {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      const index = eventListeners.indexOf(callback);
      if (index > -1) {
        eventListeners.splice(index, 1);
      }
    }
  }

  /**
   * Emit event to listeners
   */
  emit(event, data) {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Event listener error:', error);
        }
      });
    }
  }

  /**
   * Request browser notification permission
   */
  async requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    }
    return Notification.permission === 'granted';
  }

  /**
   * Disconnect WebSocket
   */
  disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'User disconnected');
      this.ws = null;
    }
    this.stopHeartbeat();
    this.isConnected = false;
  }

  /**
   * Get connection status
   */
  getStatus() {
    return {
      connected: this.isConnected,
      reconnectAttempts: this.reconnectAttempts,
      queuedMessages: this.messageQueue.length
    };
  }
}

// Export singleton instance
export default new WebSocketService();
