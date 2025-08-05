/**
 * TeoCoin Withdrawal Widget
 * 
 * Embeddable JavaScript component that adds TeoCoin withdrawal functionality
 * to existing dashboard interfaces.
 * 
 * Usage:
 * 1. Include this script in your dashboard pages
 * 2. Add <div id="teocoin-withdrawal-widget"></div> where you want the widget
 * 3. Call TeoCoinWidget.init() after page load
 */

class TeoCoinWithdrawalWidget {
    constructor() {
        this.web3 = null;
        this.userAccount = null;
        this.contract = null;
        this.userBalance = null;
        
        // Contract details
        this.POLYGON_AMOY_CHAIN_ID = '0x13882';
        this.TEOCOIN_CONTRACT = '0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8';
        this.TEOCOIN_ABI = [
            {
                "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "decimals",
                "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
                "stateMutability": "view",
                "type": "function"
            }
        ];
    }

    async init() {
        console.log('🎯 Initializing TeoCoin Withdrawal Widget...');
        
        // Get user dashboard data first
        try {
            await this.loadUserData();
            this.render();
            this.attachEventListeners();
            console.log('✅ TeoCoin Widget initialized successfully');
        } catch (error) {
            console.error('❌ Failed to initialize TeoCoin Widget:', error);
            this.renderError('Failed to load TeoCoin data');
        }
    }

    async loadUserData() {
        // Try to determine user role and load appropriate dashboard data
        const endpoints = [
            '/api/v1/dashboard/student/',
            '/api/v1/dashboard/teacher/',
            '/api/v1/dashboard/admin/'
        ];

        for (const endpoint of endpoints) {
            try {
                const response = await fetch(endpoint, {
                    headers: {
                        'Authorization': this.getAuthHeader(),
                        'Content-Type': 'application/json'
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    this.userBalance = data.teocoin_balance;
                    this.userWallet = data.wallet_address;
                    console.log('✅ Loaded user data:', data);
                    return;
                }
            } catch (error) {
                console.log(`Endpoint ${endpoint} not accessible:`, error.message);
            }
        }

        throw new Error('Could not load user dashboard data from any endpoint');
    }

    getAuthHeader() {
        // Try different auth methods
        const token = localStorage.getItem('authToken') || 
                     localStorage.getItem('access_token') ||
                     sessionStorage.getItem('authToken');
        
        if (token) {
            return `Bearer ${token}`;
        }

        // Check for Django session auth (cookies)
        return '';
    }

    render() {
        const container = document.getElementById('teocoin-withdrawal-widget');
        if (!container) {
            console.warn('TeoCoin widget container not found');
            return;
        }

        const canWithdraw = this.userBalance?.can_withdraw || false;
        const availableBalance = this.userBalance?.available || '0.00';
        const pendingWithdrawal = this.userBalance?.pending_withdrawal || '0.00';

        container.innerHTML = `
            <div class="teocoin-widget">
                <div class="teocoin-header">
                    <h3>💰 TeoCoin Withdrawal</h3>
                    <div class="balance-info">
                        <div class="balance-item">
                            <span class="label">Available:</span>
                            <span class="value">${availableBalance} TEO</span>
                        </div>
                        ${pendingWithdrawal !== '0.00' ? `
                            <div class="balance-item pending">
                                <span class="label">Pending:</span>
                                <span class="value">${pendingWithdrawal} TEO</span>
                            </div>
                        ` : ''}
                    </div>
                </div>

                <div class="teocoin-actions">
                    ${canWithdraw ? `
                        <button id="connect-metamask" class="btn btn-primary">
                            🦊 Connect MetaMask
                        </button>
                        <button id="withdraw-teocoin" class="btn btn-success" style="display: none;">
                            💸 Withdraw TEO
                        </button>
                    ` : `
                        <div class="no-withdrawal">
                            <p>⚠️ Minimum 10 TEO required for withdrawal</p>
                            <p>Current balance: ${availableBalance} TEO</p>
                        </div>
                    `}
                </div>

                <div class="wallet-status" id="wallet-status" style="display: none;">
                    <p>Wallet: <span id="wallet-address">Not connected</span></p>
                    <p>Network: <span id="network-status">Unknown</span></p>
                </div>

                <div id="withdrawal-messages"></div>
            </div>
        `;

        this.addStyles();
    }

    addStyles() {
        if (document.getElementById('teocoin-widget-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'teocoin-widget-styles';
        styles.textContent = `
            .teocoin-widget {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
                margin: 15px 0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }

            .teocoin-header h3 {
                margin: 0 0 15px 0;
                color: #495057;
                font-size: 1.2em;
            }

            .balance-info {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 10px;
                margin-bottom: 15px;
            }

            .balance-item {
                background: white;
                padding: 10px;
                border-radius: 5px;
                border-left: 4px solid #007bff;
            }

            .balance-item.pending {
                border-left-color: #ffc107;
            }

            .balance-item .label {
                display: block;
                font-size: 0.9em;
                color: #6c757d;
                margin-bottom: 5px;
            }

            .balance-item .value {
                display: block;
                font-weight: bold;
                font-size: 1.1em;
                color: #495057;
            }

            .teocoin-actions {
                margin: 15px 0;
            }

            .teocoin-widget .btn {
                background: linear-gradient(135deg, #007bff, #0056b3);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1em;
                margin-right: 10px;
                margin-bottom: 10px;
                transition: transform 0.2s;
            }

            .teocoin-widget .btn:hover {
                transform: translateY(-1px);
            }

            .teocoin-widget .btn.btn-success {
                background: linear-gradient(135deg, #28a745, #1e7e34);
            }

            .teocoin-widget .btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }

            .wallet-status {
                background: #e9ecef;
                padding: 10px;
                border-radius: 5px;
                font-size: 0.9em;
            }

            .wallet-status p {
                margin: 5px 0;
            }

            .no-withdrawal {
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                padding: 15px;
                border-radius: 5px;
                color: #856404;
            }

            .no-withdrawal p {
                margin: 5px 0;
            }

            .alert {
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
            }

            .alert-success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }

            .alert-error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }

            .alert-info {
                background: #cce7ff;
                color: #004085;
                border: 1px solid #b3d7ff;
            }
        `;

        document.head.appendChild(styles);
    }

    attachEventListeners() {
        const connectBtn = document.getElementById('connect-metamask');
        const withdrawBtn = document.getElementById('withdraw-teocoin');

        if (connectBtn) {
            connectBtn.addEventListener('click', () => this.connectMetaMask());
        }

        if (withdrawBtn) {
            withdrawBtn.addEventListener('click', () => this.showWithdrawalModal());
        }
    }

    async connectMetaMask() {
        try {
            if (typeof window.ethereum === 'undefined') {
                this.showMessage('MetaMask is not installed. Please install MetaMask to continue.', 'error');
                return;
            }

            // Load Web3 if not already loaded
            if (!window.Web3) {
                await this.loadWeb3();
            }

            this.web3 = new Web3(window.ethereum);
            
            // Request account access
            const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
            this.userAccount = accounts[0];

            // Check network
            const chainId = await window.ethereum.request({ method: 'eth_chainId' });
            if (chainId !== this.POLYGON_AMOY_CHAIN_ID) {
                await this.switchToPolygonAmoy();
            }

            // Update UI
            document.getElementById('wallet-address').textContent = 
                `${this.userAccount.substring(0, 6)}...${this.userAccount.substring(38)}`;
            document.getElementById('network-status').textContent = 'Polygon Amoy';
            document.getElementById('wallet-status').style.display = 'block';
            document.getElementById('connect-metamask').style.display = 'none';
            document.getElementById('withdraw-teocoin').style.display = 'inline-block';

            this.showMessage('MetaMask connected successfully!', 'success');

        } catch (error) {
            console.error('MetaMask connection error:', error);
            this.showMessage('Failed to connect MetaMask. Please try again.', 'error');
        }
    }

    async switchToPolygonAmoy() {
        try {
            await window.ethereum.request({
                method: 'wallet_switchEthereumChain',
                params: [{ chainId: this.POLYGON_AMOY_CHAIN_ID }]
            });
        } catch (error) {
            if (error.code === 4902) {
                // Network not added, add it
                await window.ethereum.request({
                    method: 'wallet_addEthereumChain',
                    params: [{
                        chainId: this.POLYGON_AMOY_CHAIN_ID,
                        chainName: 'Polygon Amoy Testnet',
                        nativeCurrency: {
                            name: 'MATIC',
                            symbol: 'MATIC',
                            decimals: 18
                        },
                        rpcUrls: ['https://rpc-amoy.polygon.technology/'],
                        blockExplorerUrls: ['https://amoy.polygonscan.com/']
                    }]
                });
            } else {
                throw error;
            }
        }
    }

    async loadWeb3() {
        return new Promise((resolve) => {
            if (window.Web3) {
                resolve();
                return;
            }

            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/web3@latest/dist/web3.min.js';
            script.onload = resolve;
            document.head.appendChild(script);
        });
    }

    showWithdrawalModal() {
        // Create a simple modal for withdrawal
        const modal = document.createElement('div');
        modal.innerHTML = `
            <div class="withdrawal-modal-overlay" style="
                position: fixed; top: 0; left: 0; right: 0; bottom: 0; 
                background: rgba(0,0,0,0.5); z-index: 10000; 
                display: flex; align-items: center; justify-content: center;
            ">
                <div class="withdrawal-modal" style="
                    background: white; padding: 30px; border-radius: 10px; 
                    max-width: 400px; width: 90%; max-height: 90vh; overflow-y: auto;
                ">
                    <h3>💸 Withdraw TeoCoin</h3>
                    <p>Available balance: <strong>${this.userBalance?.available || '0.00'} TEO</strong></p>
                    
                    <div style="margin: 20px 0;">
                        <label for="withdrawal-amount">Amount to withdraw:</label>
                        <input type="number" id="withdrawal-amount" 
                               min="10" max="${this.userBalance?.available || 0}" 
                               step="0.01" placeholder="Minimum 10 TEO"
                               style="width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px;">
                    </div>

                    <div style="margin: 20px 0;">
                        <label for="wallet-addr">Wallet address:</label>
                        <input type="text" id="wallet-addr" value="${this.userAccount || ''}"
                               style="width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px;">
                    </div>

                    <div style="display: flex; gap: 10px; margin-top: 20px;">
                        <button onclick="this.closest('.withdrawal-modal-overlay').remove()" 
                                style="flex: 1; padding: 10px; background: #6c757d; color: white; border: none; border-radius: 5px; cursor: pointer;">
                            Cancel
                        </button>
                        <button id="confirm-withdrawal"
                                style="flex: 1; padding: 10px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer;">
                            Confirm Withdrawal
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Handle withdrawal confirmation
        modal.querySelector('#confirm-withdrawal').addEventListener('click', () => {
            this.processWithdrawal(modal);
        });
    }

    async processWithdrawal(modal) {
        const amount = document.getElementById('withdrawal-amount').value;
        const walletAddress = document.getElementById('wallet-addr').value;

        if (!amount || amount < 10) {
            this.showMessage('Minimum withdrawal amount is 10 TEO', 'error');
            return;
        }

        if (!walletAddress) {
            this.showMessage('Please provide a wallet address', 'error');
            return;
        }

        try {
            // Show loading state
            const confirmBtn = modal.querySelector('#confirm-withdrawal');
            confirmBtn.textContent = 'Processing...';
            confirmBtn.disabled = true;

            // Make withdrawal request to backend
            const response = await fetch('/blockchain/v2/request-withdrawal/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': this.getAuthHeader(),
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    amount: parseFloat(amount),
                    wallet_address: walletAddress
                })
            });

            const result = await response.json();

            if (result.success) {
                modal.remove();
                this.showMessage(
                    `Withdrawal request submitted successfully! Your ${amount} TEO will be processed within 5-10 minutes.`, 
                    'success'
                );
                
                // Refresh user data
                await this.loadUserData();
                this.render();
                this.attachEventListeners();
            } else {
                this.showMessage(`Withdrawal failed: ${result.error}`, 'error');
                confirmBtn.textContent = 'Confirm Withdrawal';
                confirmBtn.disabled = false;
            }

        } catch (error) {
            console.error('Withdrawal error:', error);
            this.showMessage('Withdrawal request failed. Please try again.', 'error');
            const confirmBtn = modal.querySelector('#confirm-withdrawal');
            confirmBtn.textContent = 'Confirm Withdrawal';
            confirmBtn.disabled = false;
        }
    }

    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }

    showMessage(text, type = 'info') {
        const messagesDiv = document.getElementById('withdrawal-messages');
        if (!messagesDiv) return;

        const messageEl = document.createElement('div');
        messageEl.className = `alert alert-${type}`;
        messageEl.textContent = text;

        messagesDiv.appendChild(messageEl);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            messageEl.remove();
        }, 5000);
    }

    renderError(message) {
        const container = document.getElementById('teocoin-withdrawal-widget');
        if (container) {
            container.innerHTML = `
                <div class="teocoin-widget">
                    <div class="alert alert-error">
                        ❌ ${message}
                    </div>
                </div>
            `;
        }
    }
}

// Global instance
window.TeoCoinWidget = new TeoCoinWithdrawalWidget();

// Auto-initialize if widget container exists
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('teocoin-withdrawal-widget')) {
        window.TeoCoinWidget.init();
    }
});

// Also try to initialize after a delay (for dynamic content)
setTimeout(() => {
    if (document.getElementById('teocoin-withdrawal-widget') && !window.TeoCoinWidget.userBalance) {
        window.TeoCoinWidget.init();
    }
}, 1000);
