const { test } = require('@playwright/test');

test('desktop screenshot', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/');
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'e2e/screenshots/desktop-dashboard.png', fullPage: true });
});

test('mobile screenshot', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto('/');
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'e2e/screenshots/mobile-dashboard.png', fullPage: true });
});

test('audit page screenshot', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/audit');
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'e2e/screenshots/desktop-audit.png', fullPage: true });
});
