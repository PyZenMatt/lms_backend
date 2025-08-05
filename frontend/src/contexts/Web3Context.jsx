import React, { createContext, useContext, useState, useEffect } from 'react';
import { ethers } from 'ethers';

const Web3Context = createContext();

export const useWeb3Context = () => {
  const context = useContext(Web3Context);
  if (!context) {
    throw new Error('useWeb3Context must be used within a Web3Provider');
  }
  return context;
};

export const Web3Provider = ({ children }) => {
  const [account, setAccount] = useState(null);
  const [web3Provider, setWeb3Provider] = useState(null);
  const [teoBalance, setTeoBalance] = useState('0');
  const [isConnecting, setIsConnecting] = useState(false);
  const [chainId, setChainId] = useState(null);

  // TeoCoin2 contract configuration (Polygon Amoy)
  const TEOCOIN_CONTRACT_ADDRESS = process.env.REACT_APP_TEOCOIN_CONTRACT_ADDRESS || '0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8';
  const POLYGON_AMOY_CHAIN_ID = 80002;

  // TeoCoin2 ABI (minimal for balance checking)
  const TEOCOIN_ABI = [
    'function balanceOf(address owner) view returns (uint256)',
    'function decimals() view returns (uint8)',
    'function symbol() view returns (string)',
    'function name() view returns (string)'
  ];

  // Connect to MetaMask
  const connectWallet = async () => {
    if (!window.ethereum) {
      throw new Error('MetaMask is not installed');
    }

    setIsConnecting(true);
    try {
      // Request account access
      const accounts = await window.ethereum.request({ 
        method: 'eth_requestAccounts' 
      });
      
      if (accounts.length === 0) {
        throw new Error('No accounts found');
      }

      const provider = new ethers.BrowserProvider(window.ethereum);
      const network = await provider.getNetwork();
      
      setAccount(accounts[0]);
      setWeb3Provider(provider);
      setChainId(network.chainId);

      // Switch to Polygon Amoy if needed
      if (network.chainId !== POLYGON_AMOY_CHAIN_ID) {
        await switchToPolygonAmoy();
      }

      // Fetch TEO balance
      await fetchTeoBalance(accounts[0], provider);

    } catch (error) {
      console.error('Failed to connect wallet:', error);
      throw error;
    } finally {
      setIsConnecting(false);
    }
  };

  // Switch to Polygon Amoy network
  const switchToPolygonAmoy = async () => {
    try {
      await window.ethereum.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: '0x13882' }], // 80002 in hex
      });
    } catch (switchError) {
      // Network not added, try to add it
      if (switchError.code === 4902) {
        await window.ethereum.request({
          method: 'wallet_addEthereumChain',
          params: [{
            chainId: '0x13882',
            chainName: 'Polygon Amoy Testnet',
            nativeCurrency: {
              name: 'MATIC',
              symbol: 'MATIC',
              decimals: 18,
            },
            rpcUrls: ['https://rpc-amoy.polygon.technology/'],
            blockExplorerUrls: ['https://amoy.polygonscan.com/'],
          }],
        });
      } else {
        throw switchError;
      }
    }
  };

  // Fetch TeoCoin balance
  const fetchTeoBalance = async (address = account, provider = web3Provider) => {
    if (!address || !provider) return;

    try {
      const contract = new ethers.Contract(TEOCOIN_CONTRACT_ADDRESS, TEOCOIN_ABI, provider);
      const balance = await contract.balanceOf(address);
      const decimals = await contract.decimals();
      const formattedBalance = ethers.formatUnits(balance, decimals);
      setTeoBalance(formattedBalance);
    } catch (error) {
      console.error('Failed to fetch TEO balance:', error);
      setTeoBalance('0');
    }
  };

  // Refresh balance (public method)
  const refreshBalance = async () => {
    if (account && web3Provider) {
      await fetchTeoBalance();
    }
  };

  // Disconnect wallet
  const disconnectWallet = () => {
    setAccount(null);
    setWeb3Provider(null);
    setTeoBalance('0');
    setChainId(null);
  };

  // Handle account changes
  useEffect(() => {
    if (window.ethereum) {
      const handleAccountsChanged = (accounts) => {
        if (accounts.length === 0) {
          disconnectWallet();
        } else if (accounts[0] !== account) {
          setAccount(accounts[0]);
          if (web3Provider) {
            fetchTeoBalance(accounts[0]);
          }
        }
      };

      const handleChainChanged = (chainId) => {
        setChainId(parseInt(chainId, 16));
        if (parseInt(chainId, 16) === POLYGON_AMOY_CHAIN_ID && account) {
          fetchTeoBalance();
        }
      };

      window.ethereum.on('accountsChanged', handleAccountsChanged);
      window.ethereum.on('chainChanged', handleChainChanged);

      return () => {
        window.ethereum.removeListener('accountsChanged', handleAccountsChanged);
        window.ethereum.removeListener('chainChanged', handleChainChanged);
      };
    }
  }, [account, web3Provider]);

  // Auto-connect if previously connected
  useEffect(() => {
    const autoConnect = async () => {
      if (window.ethereum) {
        try {
          const accounts = await window.ethereum.request({ 
            method: 'eth_accounts' 
          });
          if (accounts.length > 0) {
            const provider = new ethers.BrowserProvider(window.ethereum);
            const network = await provider.getNetwork();
            
            setAccount(accounts[0]);
            setWeb3Provider(provider);
            setChainId(network.chainId);
            
            if (network.chainId === POLYGON_AMOY_CHAIN_ID) {
              await fetchTeoBalance(accounts[0], provider);
            }
          }
        } catch (error) {
          console.error('Auto-connect failed:', error);
        }
      }
    };

    autoConnect();
  }, []);

  const value = {
    account,
    web3Provider,
    teoBalance,
    isConnecting,
    chainId,
    connectWallet,
    disconnectWallet,
    refreshBalance,
    switchToPolygonAmoy,
    isConnected: !!account,
    isCorrectNetwork: chainId === POLYGON_AMOY_CHAIN_ID,
    TEOCOIN_CONTRACT_ADDRESS,
    POLYGON_AMOY_CHAIN_ID
  };

  return (
    <Web3Context.Provider value={value}>
      {children}
    </Web3Context.Provider>
  );
};
