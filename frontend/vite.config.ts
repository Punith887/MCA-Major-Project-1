import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          const modulePath = id.replaceAll("\\", "/").split("/node_modules/")[1] ?? "";
          if (modulePath.startsWith("recharts/")) return "recharts";
          if (/^(d3-|victory-vendor\/)/.test(modulePath)) return "chart-vendor";
          if (/^(react\/|react-dom\/|react-router-dom\/|scheduler\/)/.test(modulePath)) {
            return "framework";
          }
          if (modulePath.startsWith("lucide-react/")) return "icons";
          if (modulePath) return "vendor";
          return undefined;
        },
      },
    },
  },
  test: {
    clearMocks: true,
  },
});
