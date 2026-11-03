import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

// Production is served by the additive loopback Python runner; no CORS bypass.
// Development defaults to Demo and intentionally has no backend proxy.
export default defineConfig({
  plugins: [react()],
  server: { allowedHosts: true },
  build: { sourcemap: false, chunkSizeWarningLimit: 400 },
  test: { environment: 'jsdom', setupFiles: ['./src/test-setup.ts'], restoreMocks: true },
});
