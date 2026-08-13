import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "/",
  plugins: [react()],
  build: {
    // Vercel's FastAPI runtime only publishes generated static files from
    // public/. The local API serves this same directory for parity.
    outDir: "../public",
    emptyOutDir: true,
    sourcemap: true,
    assetsDir: "career-game/assets",
  },
  server: {
    port: 5174,
    proxy: {
      "/api": "http://127.0.0.1:8010",
      "/sprites": "http://127.0.0.1:8010",
      "/poke": "http://127.0.0.1:8010",
    },
  },
});
