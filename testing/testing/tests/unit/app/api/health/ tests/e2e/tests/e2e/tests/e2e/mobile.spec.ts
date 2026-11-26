
import { test, expect } from '@playwright/test';

test('Mobile viewport compatibility', async ({ page }) => {
  await page.setViewportSize({
    width: 390,
    height: 844
  });

  await page.goto('/');

  await expect(page.locator('body')).toBeVisible();

  const dimensions = await page.evaluate(() => ({
    screen: document.documentElement.clientWidth,
    content: document.documentElement.scrollWidth
  }));

  expect(dimensions.content).toBeLessThanOrEqual(
    dimensions.screen + 1
  );
});
