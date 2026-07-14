import { existsSync } from 'node:fs';
import { defineConfig, devices, type PlaywrightTestConfig } from '@playwright/test';
import dotenv from 'dotenv';

dotenv.config({ path: '../../.env' });

const chromiumExecutableCandidates = [
  process.env.CHROMIUM_EXECUTABLE_PATH,
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
].filter((value): value is string => Boolean(value));

const chromiumExecutablePath = chromiumExecutableCandidates.find((candidate) => existsSync(candidate));

const projects: PlaywrightTestConfig['projects'] = [
  {
    name: 'chromium',
    use: {
      ...devices['Desktop Chrome'],
      ...(chromiumExecutablePath
        ? {
            launchOptions: {
              executablePath: chromiumExecutablePath
            }
          }
        : {})
    }
  }
];

if (process.env.ENABLE_FIREFOX === '1') {
  projects.push({
    name: 'firefox',
    use: { ...devices['Desktop Firefox'] }
  });
}

export default defineConfig({
  testDir: './specs',
  timeout: 60_000,
  retries: 2,
  workers: process.env.CI ? 2 : 4,
  testIgnore: ['**/prototype/**/*.spec.ts'],
  reporter: [
    ['html', { outputFolder: './reports/html', open: 'never' }],
    ['json', { outputFile: './reports/raw/result.json' }]
  ],
  globalSetup: './global-setup.ts',
  use: {
    baseURL: process.env.BASE_URL || 'http://192.168.2.97:6089',
    storageState: './.auth/user.json',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  },
  projects
});
