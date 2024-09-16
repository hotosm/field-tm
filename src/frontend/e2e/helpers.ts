import { Page } from '@playwright/test';

export async function tempLogin(page: Page) {
  await page.goto('/');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByText('Temporary Account').click();
}

export async function openFirstProject(page: Page) {
  // click first project card on the home page
  await page.locator('.MuiCardContent-root').first().click();
  await page.waitForTimeout(4000);
}
