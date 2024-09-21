import { Page } from '@playwright/test';

export async function tempLogin(page: Page) {
  await page.goto('/');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByText('Temporary Account').click();
}

export async function openTestProject(page: Page) {
  // open project card with regex text 'Project Create Playwright xxx'
  await page
    .getByText(/^Project Create Playwright/)
    .first()
    .click();
  await page.waitForTimeout(4000);
}
