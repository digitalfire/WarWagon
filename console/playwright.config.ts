import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir:'./e2e',use:{baseURL:'http://127.0.0.1:5173',headless:true},
  webServer:[
    {command:'python -m warwagon.console_api --port 8765',cwd:'..',url:'http://127.0.0.1:8765/api/v1/health',reuseExistingServer:!process.env.CI,timeout:60000},
    {command:'npm run dev -- --port 5173 --strictPort',url:'http://127.0.0.1:5173',reuseExistingServer:!process.env.CI,timeout:60000},
  ],
});
