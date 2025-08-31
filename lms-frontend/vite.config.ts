import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import path from "path"

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
  "@": path.resolve(__dirname, "./src"),
  "@/components/ui": path.resolve(__dirname, "./src/components/ui"),
  "@/components/figma/ui": path.resolve(__dirname, "./src/components/figma/ui"),
  "@onchain": path.resolve(__dirname, "./src/web3"),
  "onchain": path.resolve(__dirname, "./src/web3"),
  // Force single React copy to avoid invalid hook call / dispatcher is null errors
  // Sometimes dependencies or symlinks can cause multiple React instances to be bundled.
  // These aliases ensure all imports resolve to the workspace root node_modules.
  "react": path.resolve(__dirname, "./node_modules/react"),
  "react-dom": path.resolve(__dirname, "./node_modules/react-dom"),
    },
  },
})
