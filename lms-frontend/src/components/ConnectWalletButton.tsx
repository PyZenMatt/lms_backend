import React from "react";
import { useWeb3 } from "@/context/Web3Context";
import { shortAddress } from "@/services/web3";

export default function ConnectWalletButton() {
  const { available, address, connect, disconnect, chainId } = useWeb3();

  if (!available) {
    return (
      <a target="_blank" rel="noreferrer" href="https://metamask.io/download.html" className="text-sm px-3 py-1 border rounded">Installa MetaMask</a>
    )
  }

  if (!address) {
    return (
      <button onClick={() => connect()} className="text-sm px-3 py-1 bg-emerald-600 text-white rounded">Connect</button>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <div className="text-sm px-2 py-1 border rounded">{shortAddress(address)}</div>
      <div className="text-xs text-muted">{chainId ?? "unknown chain"}</div>
      <button onClick={() => disconnect()} className="text-sm px-2 py-1 border rounded">Disconnect</button>
    </div>
  )
}
