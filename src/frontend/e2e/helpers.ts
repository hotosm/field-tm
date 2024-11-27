import { Page } from '@playwright/test';

export async function openTestProject(page: Page) {
  await page.goto('/');
  // open project card with regex text 'Project Create Playwright xxx'
  await page
    .getByText(/^Project Create Playwright/)
    .first()
    .click();
  await page.waitForTimeout(4000);
}
