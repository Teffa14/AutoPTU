import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "/career-game/",
  plugins: [react()],
  build: {
    // Vercel's FastAPI runtime only publishes generated static files from
    // public/. The local API serves this same directory for parity.
    outDir: "../public/career-game",
    // Keep the versioned CDN files present while the remote build overwrites
    // them; Vercel discovers public/ before it runs the build command.
    emptyOutDir: false,
    sourcemap: false,
    assetsDir: "assets",
    rollupOptions: {
      output: {
        entryFileNames: "assets/app.js",
        chunkFileNames: "assets/[name].js",
        assetFileNames: "assets/[name][extname]",
      },
    },
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
