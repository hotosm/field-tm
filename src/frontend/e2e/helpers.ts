import { Page } from '@playwright/test';

export async function tempLogin(page: Page) {
  await page.goto('/');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByText('Temporary Account').click();
}
