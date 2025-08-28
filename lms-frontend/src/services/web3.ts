// src/services/web3.ts
/* Minimal EIP-1193 wiring used by the Teacher Inbox MVP.
 * - ensureProvider: verifies window.ethereum exists
 * - connectWallet: requests accounts
 * - ensureChain: switches/adds chain using VITE_* env vars
 * - sendTx: eth_sendTransaction + polling for receipt
 */
type SendTxInput = { to: string; data?: string | null; value?: string | null; chainId?: string | number }

function shortHex(h?: string) { if (!h) return ""; return h.slice(0,6)+"..."+h.slice(-4) }

export function ensureProvider(): boolean {
  if (typeof window === "undefined") return false
  // @ts-ignore
  return !!(window.ethereum && typeof window.ethereum.request === "function")
}

export async function connectWallet(): Promise<{ ok: boolean; address?: string; error?: any }> {
  try {
    // @ts-ignore
    const accounts: string[] = await window.ethereum.request({ method: "eth_requestAccounts" })
    const a = Array.isArray(accounts) && accounts.length ? accounts[0] : undefined
    return { ok: true, address: a }
  } catch (err) {
    return { ok: false, error: err }
  }
}

export async function ensureChain(chainIdHex: string): Promise<{ ok: boolean; switched?: boolean; error?: any }> {
  if (!chainIdHex) return { ok: false, error: "chainId required" }
  try {
    // @ts-ignore
    const current = await window.ethereum.request({ method: "eth_chainId" })
    if (current === chainIdHex) return { ok: true, switched: false }
    try {
      // try switch
      // @ts-ignore
      await window.ethereum.request({ method: "wallet_switchEthereumChain", params: [{ chainId: chainIdHex }] })
      return { ok: true, switched: true }
    } catch (switchErr: any) {
      // user rejected or chain not added (4902)
      // try add using VITE vars
      const rpc = import.meta.env.VITE_CHAIN_RPC_URL
      const name = import.meta.env.VITE_CHAIN_NAME
      const symbol = import.meta.env.VITE_CHAIN_SYMBOL
      if (!rpc || !name) return { ok: false, error: switchErr }
      try {
        // @ts-ignore
        await window.ethereum.request({
          method: "wallet_addEthereumChain",
          params: [
            {
              chainId: chainIdHex,
              chainName: name,
              nativeCurrency: { name: symbol || name, symbol: symbol || "ETH", decimals: 18 },
              rpcUrls: [rpc],
              blockExplorerUrls: [import.meta.env.VITE_EXPLORER_URL || ""].filter(Boolean),
            },
          ],
        })
        return { ok: true, switched: true }
      } catch (addErr) {
        return { ok: false, error: addErr }
      }
    }
  } catch (err) {
    return { ok: false, error: err }
  }
}

export async function sendTx(input: SendTxInput): Promise<{ ok: boolean; hash?: string; status?: "success"|"failed"; error?: any }> {
  try {
    const params: any = { to: input.to }
    if (input.data) params.data = input.data
    if (input.value) params.value = input.value
    // Ensure chain is correct is caller responsibility
    // @ts-ignore
    const txHash: string = await window.ethereum.request({ method: "eth_sendTransaction", params: [params] })
    // poll for receipt
    const start = Date.now()
    const timeout = 2 * 60 * 1000 // 2 minutes
    while (Date.now() - start < timeout) {
      // @ts-ignore
      const receipt = await window.ethereum.request({ method: "eth_getTransactionReceipt", params: [txHash] })
      if (receipt) {
        const ok = receipt.status === "0x1" || receipt.status === 1
        return { ok: ok, hash: txHash, status: ok ? "success" : "failed" }
      }
      await new Promise((r) => setTimeout(r, 3500))
    }
    return { ok: false, hash: txHash, status: "failed", error: "timeout" }
  } catch (err) {
    return { ok: false, error: err }
  }
}

export function shortAddress(addr?: string) { if (!addr) return ""; return addr.slice(0,6)+"..."+addr.slice(-4) }
