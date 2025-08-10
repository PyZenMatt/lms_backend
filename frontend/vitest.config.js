import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/setupTests.js'],
    coverage: {
      reporter: ['text', 'html'],
      exclude: ['**/*.d.ts', '**/__tests__/**'],
    },
    globals: true,
  exclude: ['tests/e2e/**'],
  }
});
