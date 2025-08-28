import React from "react";
import { ensureProvider, connectWallet, shortAddress, ensureChain } from "@/services/web3";

type Web3Ctx = {
  available: boolean;
  address?: string | null;
  chainId?: string | null;
  connect: () => Promise<void>;
  disconnect: () => void;
  ensureChain: (chainIdHex: string) => Promise<{ ok: boolean; switched?: boolean; error?: any }>;
}

const Ctx = React.createContext<Web3Ctx | undefined>(undefined);
export const useWeb3 = () => {
  const c = React.useContext(Ctx);
  if (!c) throw new Error("useWeb3 outside provider")
  return c;
}

export function Web3Provider({ children }: { children: React.ReactNode }) {
  const [available] = React.useState<boolean>(ensureProvider());
  const [address, setAddress] = React.useState<string | null>(null);
  const [chainId, setChainId] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!available) return;
    // @ts-ignore
    const handleAccounts = (accs: string[]) => setAddress(accs && accs.length ? accs[0] : null);
    // @ts-ignore
    const handleChain = (c: string) => setChainId(c ?? null);
    try {
      // @ts-ignore
      window.ethereum?.request?.({ method: "eth_accounts" }).then((accs: string[]) => handleAccounts(accs)).catch(()=>{})
      // @ts-ignore
      window.ethereum?.request?.({ method: "eth_chainId" }).then((c: string) => handleChain(c)).catch(()=>{})
      // @ts-ignore
      window.ethereum?.on?.("accountsChanged", handleAccounts)
      // @ts-ignore
      window.ethereum?.on?.("chainChanged", handleChain)
    } catch {}

    return () => {
      try {
        // @ts-ignore
        window.ethereum?.removeListener?.("accountsChanged", handleAccounts)
        // @ts-ignore
        window.ethereum?.removeListener?.("chainChanged", handleChain)
      } catch {}
    }
  }, [available]);

  async function doConnect() {
    if (!available) return;
    const r = await connectWallet();
    if (r.ok) setAddress(r.address ?? null);
  }

  function disconnect() { setAddress(null) }

  return (
    <Ctx.Provider value={{ available, address, chainId, connect: doConnect, disconnect, ensureChain }}>
      {children}
    </Ctx.Provider>
  )
}
