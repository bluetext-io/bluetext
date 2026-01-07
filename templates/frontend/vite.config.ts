import { reactRouter } from "@react-router/dev/vite";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";
import path from "path";

export default defineConfig({
  resolve: {
    // Explicit aliases for reliable module resolution in both dev and SSR
    // While tsconfigPaths plugin reads from tsconfig.json, explicit aliases
    // ensure consistent resolution timing, especially for @ (root) imports
    alias: {
      '@': path.resolve(__dirname, '.'),
      '~': path.resolve(__dirname, './app'),
    },
  },
  plugins: [tailwindcss(), reactRouter(), tsconfigPaths()],
});
