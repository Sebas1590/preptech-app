import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { TanStackRouterVite } from "@tanstack/router-plugin/vite";
import tailwindcss from "@tailwindcss/vite";
import path from "path"; 

export default defineConfig({
  plugins: [
    tailwindcss(),
    TanStackRouterVite(),
    react(),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    open: true,
    proxy: { "/api": process.env["VITE_PROXY_TARGET"] ?? "http://localhost:8000" },
  }
});