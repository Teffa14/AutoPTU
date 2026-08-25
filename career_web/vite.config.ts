import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const base = process.env.VITE_BASE_PATH ?? "/career-game/";

export default defineConfig({
  base,
  plugins: [react()],
  build: {
    outDir: "../public/career-game",
    emptyOutDir: true,
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
