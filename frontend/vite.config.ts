import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server binds 0.0.0.0 so it is reachable from the host when run in Docker.
export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
  },
});
