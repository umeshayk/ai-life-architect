import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  testMatch: 'app-shell.spec.ts',
  use: {
    baseURL: 'http://127.0.0.1:5176',
    headless: true,
  },
  webServer: {
    command: 'C:\\nvm4w\\nodejs\\npm.cmd run dev -- --host 127.0.0.1 --port 5176',
    url: 'http://127.0.0.1:5176',
    reuseExistingServer: true,
    timeout: 120000,
  },
});
