
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],

  test: {
    environment: 'jsdom',
    globals: true,
    include: ['tests/unit/**/*.test.ts',
              'tests/unit/**/*.test.tsx'],

    reporters: ['default', 'json'],
    outputFile: {
      json: './test-results/unit-results.json'
    }
  }
});
