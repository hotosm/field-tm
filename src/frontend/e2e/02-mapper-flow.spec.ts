import { test, expect } from '@playwright/test';

test.describe('mapper flow', () => {
  test('mapper flow', async ({ page }) => {
    await page.goto('/');
    // await page.goto('http://fmtm.localhost:7050/');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await page
      .getByLabel('', { exact: true })
      .locator('div')
      .filter({ hasText: "Temporary AccountIf you're" })
      .nth(3)
      .click();

    // click first project card on the home page
    await page.locator('.MuiCardContent-root').first().click();

    // click on task
    await page.waitForTimeout(4000);
    await page.locator('canvas').click({
      position: {
        x: 445,
        y: 95,
      },
    });
    await expect(page.getByText('Status: READY')).toBeVisible();
    await page.getByRole('alert').waitFor({ state: 'hidden' });
    await page.getByTitle('Close').getByTestId('CloseIcon').click();
    expect(await page.locator('canvas').screenshot()).toMatchSnapshot('ready.png');

    await page.locator('canvas').click({
      position: {
        x: 445,
        y: 95,
      },
    });
    // STATUS: READY
    await page.getByRole('button', { name: 'START MAPPING' }).waitFor({ state: 'visible' });
    await page.getByRole('button', { name: 'START MAPPING' }).click();
    await page.waitForSelector('div:has-text("updated status to LOCKED_FOR_MAPPING"):nth-of-type(1)');
    await expect(
      page
        .locator('div')
        .filter({ hasText: /updated status to LOCKED_FOR_MAPPING/ })
        .first(),
    ).toBeVisible();
    await page.getByRole('alert').waitFor({ state: 'hidden' });
    await page.getByTitle('Close').getByTestId('CloseIcon').click();
    expect(await page.locator('canvas').screenshot()).toMatchSnapshot('locked-for-mapping.png');

    await page.locator('canvas').click({
      position: {
        x: 445,
        y: 95,
      },
    });
    //STATUS: LOCKED_FOR_MAPPING
    await page.getByRole('button', { name: 'MARK AS FULLY MAPPED' }).click();
    await page.getByRole('button', { name: 'MARK AS FULLY MAPPED' }).click();
    await page.waitForSelector('div:has-text("updated status to MAPPED"):nth-of-type(1)');
    await expect(
      page
        .locator('div')
        .filter({ hasText: /updated status to MAPPED/ })
        .first(),
    ).toBeVisible();
    await page.getByRole('alert').waitFor({ state: 'hidden' });
    await page.getByTitle('Close').getByTestId('CloseIcon').click();
    expect(await page.locator('canvas').screenshot()).toMatchSnapshot('mapped.png');

    await page.locator('canvas').click({
      position: {
        x: 445,
        y: 95,
      },
    });
    // STATUS: MAPPED
    await page.getByRole('button', { name: 'START VALIDATION' }).click();
    await page.getByRole('button', { name: 'FULLY MAPPED' }).click();

    await page.getByText('has been updated to VALIDATED').waitFor({ state: 'visible' });
    await expect(page.getByText('has been updated to VALIDATED')).toBeVisible();

    // click on validated task after map renders
    await page.waitForTimeout(4000);
    expect(await page.locator('canvas').screenshot()).toMatchSnapshot('validated.png');
    await page.locator('canvas').click({
      position: {
        x: 445,
        y: 95,
      },
    });
    await expect(page.getByText('Status: VALIDATED')).toBeVisible();
  });

  test('comment section', async ({ page }) => {
    await page.goto('/');
    // await page.goto('http://fmtm.localhost:7050/');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await page
      .getByLabel('', { exact: true })
      .locator('div')
      .filter({ hasText: "Temporary AccountIf you're" })
      .nth(3)
      .click();

    // click first project card on the home page
    await page.locator('.MuiCardContent-root').first().click();

    await page.waitForTimeout(4000);
    await page.locator('canvas').click({
      position: {
        x: 475,
        y: 127,
      },
    });

    // Assert no comment is visible
    await page.getByRole('button', { name: 'Comments' }).click();
    await expect(page.getByText('No Comments!')).toBeVisible();

    // Add comment
    await page.getByTestId('FormatBoldIcon').click();
    await page.locator('.fmtm-min-h-\\[150px\\] > .tiptap > p').click();
    await page.locator('.fmtm-min-h-\\[150px\\] > .tiptap').fill('Test playwright');
    await page.getByRole('button', { name: 'SAVE COMMENT' }).click();
    await expect(
      page
        .locator('div')
        .filter({ hasText: /Test playwright/ })
        .first(),
    ).toBeVisible();

    // Add comment
    await page.locator('.fmtm-min-h-\\[150px\\] > .tiptap > p').click();
    await page.locator('.fmtm-min-h-\\[150px\\] > .tiptap > p').click();
    await page.locator('.fmtm-min-h-\\[150px\\] > .tiptap').fill('map features accurately');
    await page.getByRole('button', { name: 'SAVE COMMENT' }).click();
    await expect(
      page
        .locator('div')
        .filter({ hasText: /map features accurately/ })
        .first(),
    ).toBeVisible();

    // Save empty comment
    await page.locator('.fmtm-min-h-\\[150px\\] > .tiptap > p').click();
    await page.getByRole('button', { name: 'SAVE COMMENT' }).click();
    await page.getByRole('heading', { name: 'Empty comment field.' }).click();
    await page.getByRole('alert').click();
  });
});
