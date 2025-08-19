/* @ts-nocheck */
/**
 * 🪙 TeoCoin Manager - Unified Component
 * Student / Teacher / Admin
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Button,
  TextField,
  Typography,
  Box,
  Alert,
  Chip,
  CircularProgress,
  Card,
  CardContent,
  Grid,
  IconButton,
  Tooltip,
  Tabs,
  Tab,
  Divider
} from '@mui/material';
import {
  AccountBalanceWallet,
  Send,
  Refresh,
  Close,
  Info,
  CheckCircle,
  LocalFireDepartment,
  AccountBalance,
  TrendingUp
} from '@mui/icons-material';
import { BrowserProvider, Contract, formatEther, parseEther } from 'ethers';
import { useAuth } from '../../contexts/AuthContext';

// TeoCoin contract configuration
const TEOCOIN_CONTRACT = '0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8';
const POLYGON_AMOY_CHAIN_ID = '0x13882'; // 80002 hex
const TEOCOIN_ABI = [
  {
    inputs: [{ internalType: 'address', name: 'account', type: 'address' }],
    name: 'balanceOf',
    outputs: [{ internalType: 'uint256', name: '', type: 'uint256' }],
    stateMutability: 'view',
    type: 'function'
  },
  {
    inputs: [],
    name: 'decimals',
    outputs: [{ internalType: 'uint8', name: '', type: 'uint8' }],
    stateMutability: 'view',
    type: 'function'
  },
  {
    inputs: [{ internalType: 'uint256', name: 'amount', type: 'uint256' }],
    name: 'burn',
    outputs: [],
    stateMutability: 'nonpayable',
    type: 'function'
  },
  {
    inputs: [
      { internalType: 'address', name: 'to', type: 'address' },
      { internalType: 'uint256', name: 'amount', type: 'uint256' }
    ],
    name: 'mintTo',
    outputs: [],
    stateMutability: 'nonpayable',
    type: 'function'
  }
];

function TeoCoinManagerInner({ open, onClose, userBalance = 0 }) {
  const { user } = useAuth();
  const [currentTab, setCurrentTab] = useState(0); // 0: Withdraw, 1: Burn, 2: Stake
  const [dbBalance, setDbBalance] = useState(userBalance);
  const [chainOk, setChainOk] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const isTeacher = user?.role === 'teacher';

  const ensureChain = useCallback(async () => {
    try {
      if (!window.ethereum) throw new Error('MetaMask non disponibile');
      const provider = new BrowserProvider(window.ethereum);
      const network = await provider.send('eth_chainId', []);
      if (network !== POLYGON_AMOY_CHAIN_ID) {
        await provider.send('wallet_switchEthereumChain', [{ chainId: POLYGON_AMOY_CHAIN_ID }]);
      }
      setChainOk(true);
    } catch (e) {
      setChainOk(false);
      setErrorMsg(e.message ?? 'Errore rete');
    }
  }, []);

  const fetchWalletBalance = useCallback(async () => {
    try {
      if (!window.ethereum) return;
      const provider = new BrowserProvider(window.ethereum);
      const signer = await provider.getSigner();
      const addr = await signer.getAddress();
      const contract = new Contract(TEOCOIN_CONTRACT, TEOCOIN_ABI, provider);
      const raw = await contract.balanceOf(addr);
      // puoi salvare in stato se ti serve
      // setWalletBalance(Number(formatEther(raw)));
    } catch (e) {
      // opzionale: gestione errore silenziosa
    }
  }, []);

  useEffect(() => {
    if (open) {
      setErrorMsg('');
      setSuccessMsg('');
      ensureChain();
      fetchWalletBalance();
    }
  }, [open, ensureChain, fetchWalletBalance]);

  const handleWithdraw = async (amount) => {
    try {
      setLoading(true);
      setErrorMsg('');
      // TODO: chiama API backend per richiesta mint → poi esegui mintTo con signer se previsto
      // setSuccessMsg("Prelievo completato");
      // setDbBalance((v) => v - amount);
    } catch (e) {
      setErrorMsg(e.message ?? 'Errore prelievo');
    } finally {
      setLoading(false);
    }
  };

  const handleBurn = async (amount) => {
    try {
      setLoading(true);
      setErrorMsg('');
      if (!window.ethereum) throw new Error('MetaMask non disponibile');
      const provider = new BrowserProvider(window.ethereum);
      const signer = await provider.getSigner();
      const contract = new Contract(TEOCOIN_CONTRACT, TEOCOIN_ABI, signer);
      await contract.burn(parseEther(String(amount)));
      // TODO: chiama backend per accreditare saldo DB
      setSuccessMsg('Burn eseguito');
    } catch (e) {
      setErrorMsg(e.message ?? 'Errore burn');
    } finally {
      setLoading(false);
    }
  };

  const handleStake = async (amount) => {
    // TODO: operazione disponibile solo per teacher
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>
        TeoCoin Manager
        <IconButton aria-label="close" onClick={onClose} sx={{ position: 'absolute', right: 8, top: 8 }}>
          <Close />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers>
        {errorMsg && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {errorMsg}
          </Alert>
        )}
        {successMsg && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {successMsg}
          </Alert>
        )}

        <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
          <Chip icon={<AccountBalance />} label={`Saldo piattaforma: ${dbBalance} TEO`} />
          <Chip
            icon={<AccountBalanceWallet />}
            label={chainOk ? 'Wallet pronto' : 'Wallet non pronto'}
            color={chainOk ? 'success' : 'default'}
          />
          <Tooltip title="Aggiorna">
            <IconButton onClick={fetchWalletBalance}>
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>

        <Tabs value={currentTab} onChange={(_, v) => setCurrentTab(v)}>
          <Tab icon={<Send />} label="Withdraw" />
          <Tab icon={<LocalFireDepartment />} label="Burn" />
          <Tab icon={<TrendingUp />} label="Stake" disabled={!isTeacher} />
        </Tabs>
        <Divider sx={{ mb: 2 }} />

        {currentTab === 0 && (
          <Box>
            <Typography variant="subtitle1" sx={{ mb: 1 }}>
              Preleva verso MetaMask
            </Typography>
            {/* form importo + Button → handleWithdraw */}
          </Box>
        )}
        {currentTab === 1 && (
          <Box>
            <Typography variant="subtitle1" sx={{ mb: 1 }}>
              Converti da MetaMask a saldo piattaforma
            </Typography>
            {/* form importo + Button → handleBurn */}
          </Box>
        )}
        {currentTab === 2 && (
          <Box>
            <Typography variant="subtitle1" sx={{ mb: 1 }}>
              Stake (solo teacher)
            </Typography>
            {/* form + Button → handleStake */}
          </Box>
        )}
      </DialogContent>
    </Dialog>
  );
}

export default function TeoCoinManager(props) {
  return <TeoCoinManagerInner {...props} />;
}
