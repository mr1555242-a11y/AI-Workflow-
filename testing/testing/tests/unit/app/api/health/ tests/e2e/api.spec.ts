
import { test, expect } from '@playwright/test';

test('API health endpoint', async ({ request }) => {
  const response = await request.get('/api/health');

  expect(response.status()).toBe(200);

  const data = await response.json();

  expect(data.status).toBe('healthy');
  expect(data.service).toBe('TestPilot AI');
});
