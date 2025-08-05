/**
 * Web3 Provider Service for Gas-Free Operations
 * Handles MetaMask connection and provider management
 */

import { ethers } from 'ethers';

class Web3ProviderService {
  constructor() {
    this.provider = null;
    this.signer = null;
    this.chainId = parseInt(process.env.REACT_APP_CHAIN_ID || '80002'); // Polygon Amoy
    this.rpcUrl = process.env.REACT_APP_RPC_URL || 'https://rpc-amoy.polygon.technology/';
  }

  /**
   * Check if MetaMask is installed
   * @returns {boolean} True if MetaMask is available
   */
  isMetaMaskInstalled() {
    return typeof window !== 'undefined' && 
           typeof window.ethereum !== 'undefined' && 
           window.ethereum.isMetaMask;
  }

  /**
   * Connect to MetaMask and get provider
   * @returns {Promise<{provider: ethers.BrowserProvider, signer: ethers.JsonRpcSigner}>}
   */
  async connectMetaMask() {
    if (!this.isMetaMaskInstalled()) {
      throw new Error('MetaMask is not installed. Please install MetaMask to continue.');
    }

    try {
      // Request account access
      await window.ethereum.request({ method: 'eth_requestAccounts' });
      
      // Create provider and signer
      this.provider = new ethers.BrowserProvider(window.ethereum);
      this.signer = await this.provider.getSigner();
      
      // Check if we're on the correct network
      const network = await this.provider.getNetwork();
      if (Number(network.chainId) !== this.chainId) {
        await this.switchToCorrectNetwork();
      }

      return {
        provider: this.provider,
        signer: this.signer
      };
    } catch (error) {
      console.error('Failed to connect to MetaMask:', error);
      throw new Error('Failed to connect to MetaMask. Please try again.');
    }
  }

  /**
   * Switch to the correct network (Polygon Amoy)
   */
  async switchToCorrectNetwork() {
    try {
      await window.ethereum.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: `0x${this.chainId.toString(16)}` }],
      });
    } catch (switchError) {
      // This error code indicates that the chain has not been added to MetaMask
      if (switchError.code === 4902) {
        try {
          await window.ethereum.request({
            method: 'wallet_addEthereumChain',
            params: [
              {
                chainId: `0x${this.chainId.toString(16)}`,
                chainName: 'Polygon Amoy Testnet',
                nativeCurrency: {
                  name: 'MATIC',
                  symbol: 'MATIC',
                  decimals: 18,
                },
                rpcUrls: [this.rpcUrl],
                blockExplorerUrls: ['https://amoy.polygonscan.com/'],
              },
            ],
          });
        } catch (addError) {
          console.error('Failed to add network:', addError);
          throw new Error('Failed to add Polygon Amoy network to MetaMask');
        }
      } else {
        console.error('Failed to switch network:', switchError);
        throw new Error('Failed to switch to Polygon Amoy network');
      }
    }
  }

  /**
   * Get current wallet address
   * @returns {Promise<string>} Current wallet address
   */
  async getCurrentAddress() {
    if (!this.signer) {
      const { signer } = await this.connectMetaMask();
      this.signer = signer;
    }
    return await this.signer.getAddress();
  }

  /**
   * Sign a message with the current wallet
   * @param {string} message - Message to sign
   * @returns {Promise<string>} Signature
   */
  async signMessage(message) {
    if (!this.signer) {
      const { signer } = await this.connectMetaMask();
      this.signer = signer;
    }
    return await this.signer.signMessage(message);
  }

  /**
   * Check if wallet is connected
   * @returns {Promise<boolean>} True if connected
   */
  async isConnected() {
    try {
      if (!this.isMetaMaskInstalled()) return false;
      
      const accounts = await window.ethereum.request({ method: 'eth_accounts' });
      return accounts.length > 0;
    } catch (error) {
      console.error('Error checking connection:', error);
      return false;
    }
  }

  /**
   * Listen for account changes
   * @param {Function} callback - Callback function for account changes
   */
  onAccountChange(callback) {
    if (this.isMetaMaskInstalled()) {
      window.ethereum.on('accountsChanged', callback);
    }
  }

  /**
   * Listen for network changes
   * @param {Function} callback - Callback function for network changes
   */
  onNetworkChange(callback) {
    if (this.isMetaMaskInstalled()) {
      window.ethereum.on('chainChanged', callback);
    }
  }

  /**
   * Remove event listeners
   */
  removeListeners() {
    if (this.isMetaMaskInstalled()) {
      window.ethereum.removeAllListeners('accountsChanged');
      window.ethereum.removeAllListeners('chainChanged');
    }
  }

  /**
   * Get a read-only provider (fallback RPC)
   * @returns {ethers.JsonRpcProvider} Read-only provider
   */
  getReadOnlyProvider() {
    return new ethers.JsonRpcProvider(this.rpcUrl);
  }
}

// Export singleton instance
export const web3Provider = new Web3ProviderService();
export default web3Provider;
