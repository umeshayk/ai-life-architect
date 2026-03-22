import { expect, test } from '@playwright/test';

test('application shell renders with navigation', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('link', { name: /ala ai life architect/i }).first()).toBeVisible();
  await expect(page.getByRole('link', { name: /dashboard/i })).toBeVisible();
  await expect(page.getByRole('heading', { name: "Today's focus" })).toBeVisible();
});
