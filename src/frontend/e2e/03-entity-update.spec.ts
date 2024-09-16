import { test, expect } from '@playwright/test';

import { tempLogin } from './helpers';

test('entity update', async ({ browserName, page }) => {
  // Specific for this large test, only run in one browser
  // (playwright.config.ts is configured to run all browsers by default)
  test.skip(browserName !== 'chromium', 'Test only for chromium!');

  await tempLogin(page);

  // click first project card on the home page
  await page.locator('.MuiCardContent-root').first().click();

  // click on task & assert task popup visibility
  await page.waitForTimeout(4000);
  await page.locator('canvas').click({
    position: {
      x: 388,
      y: 220,
    },
  });
  await expect(page.getByText('Status: READY')).toBeVisible();
  await expect(page.getByRole('button', { name: 'START MAPPING' })).toBeVisible();

  // click on entity within task & assert feature popup visibility
  await page.waitForTimeout(4000);
  await page.locator('canvas').click({
    position: {
      x: 387,
      y: 211,
    },
  });
  await expect(page.getByRole('heading', { name: 'Feature:' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'MAP FEATURE IN ODK' })).toBeEnabled();
  await page.getByRole('button', { name: 'MAP FEATURE IN ODK' }).click();
  await expect(
    page.getByRole('alert').locator('div').filter({ hasText: 'Requires a mobile phone with ODK collect' }),
  ).toBeVisible();

  // check if task status is updated to locked_for_mapping on entity map
  await page.waitForSelector('div:has-text("updated status to LOCKED_FOR_MAPPING"):nth-of-type(1)');
  await expect(
    page
      .locator('div')
      .filter({ hasText: /updated status to LOCKED_FOR_MAPPING/ })
      .first(),
  ).toBeVisible();

  // click on task to check if task popup has been updated
  await page.waitForTimeout(4000);
  await page.locator('canvas').click({
    position: {
      x: 411,
      y: 171,
    },
  });

  // await page.getByText('Status: LOCKED_FOR_MAPPING').click();
  await expect(page.getByText('Status: LOCKED_FOR_MAPPING')).toBeVisible();

  // click entity to confirm task is locked
  await page.locator('canvas').click({
    position: {
      x: 387,
      y: 211,
    },
  });
  await expect(page.getByRole('button', { name: 'MAP FEATURE IN ODK' })).toBeDisabled();
});
