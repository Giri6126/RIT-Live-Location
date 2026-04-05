import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
    hmr: {
      overlay: false,
    },
    proxy: {
      // Forward all /api/* requests to the Flask backend during development
      "/api": {
        target: "http://127.0.0.1:5000",
        changeOrigin: true,
        secure: false,
      },
    },
  },
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  optimizeDeps: {
    force: true,
    include: ["react", "react-dom", "react-leaflet", "@react-leaflet/core"],
  },
  resolve: {
    dedupe: ["react", "react-dom"],
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
