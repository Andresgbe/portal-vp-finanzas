import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    // En desarrollo el navegador solo habla con Vite (mismo origen), y Vite reenvía
    // /api al backend. Así la cookie SameSite=Strict funciona sin abrir CORS.
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
