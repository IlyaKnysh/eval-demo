import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for the Storefront Admin E2E suite.
 *
 * Environment values (base URL, credentials) are supplied via .env / CI
 * secrets — see .env.example. No environment or credential is hardcoded here.
 */
export default defineConfig({
  testDir: './tests',
  outputDir: './test-results',
  timeout: 30_000,
  expect: {
    timeout: 5_000,
  },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,

  // Zero retries by default: flaky tests should be fixed, not hidden by
  // retrying. See CONTRIBUTING.md "No-retry policy" for rationale.
  retries: 0,

  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['list'],
    ...(process.env.CI ? [['github'] as const] : []),
  ],

  use: {
    baseURL: process.env.BASE_URL ?? 'http://localhost:3000',
    // retries is 0 by policy, so 'on-first-retry' would never fire —
    // capture on failure instead.
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10_000,
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],
});
