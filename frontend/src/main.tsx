import React from "react";
import { createRoot } from "react-dom/client";

import { ConfigProvider } from "./contexts/ConfigContext";
import { AuthProvider } from "./components/AuthContext";
import { Web3Provider } from "./contexts/Web3Context";
import { NotificationProvider } from "./contexts/NotificationContext";

// Ordine CSS: tokens → tema V2 → Tailwind
import "@/styles/tokens.css";
import "@/styles/v2.css";
import "@/styles/globals.css";

import App from "./App";
import { AppErrorBoundary } from "./components/system/AppErrorBoundary";
import { installGlobalErrorListeners } from "./system/error-listeners";
import { interceptConsole } from "./system/console-interceptor";
import reportWebVitals from "./reportWebVitals";

// Tema V2 il prima possibile
document.documentElement.setAttribute("data-theme", "v2");

// Telemetria minimale in dev
const send = (payload: unknown) => {
  if ((import.meta as any)?.env?.DEV) {
    // eslint-disable-next-line no-console
    console.log("[telemetry]", payload);
  }
};
installGlobalErrorListeners(send as any);
interceptConsole(send as any);

// Mount unico
const container = document.getElementById("root");
if (!container) throw new Error("Root container #root not found");
const root = createRoot(container);

root.render(
  <ConfigProvider>
    <AuthProvider>
      <Web3Provider>
        <NotificationProvider>
          <AppErrorBoundary>
            <App />
          </AppErrorBoundary>
        </NotificationProvider>
      </Web3Provider>
    </AuthProvider>
  </ConfigProvider>
);

// Se non ti servono metriche ora, niente callback:
reportWebVitals();
