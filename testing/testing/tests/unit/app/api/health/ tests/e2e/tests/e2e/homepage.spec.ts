
import { test, expect } from '@playwright/test';

test('Homepage loads', async ({ page }) => {
  await page.goto('/');

  await expect(page.locator('body')).toBeVisible();

  const title = await page.title();
  expect(title.length).toBeGreaterThan(0);
});

test('Page has no uncaught JavaScript errors', async ({ page }) => {
  const errors: string[] = [];

  page.on('pageerror', error => {
    errors.push(error.message);
  });

  await page.goto('/');
  await page.waitForLoadState('networkidle');

  expect(errors).toEqual([]);
});
          
