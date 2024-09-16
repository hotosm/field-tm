import { test, expect } from '@playwright/test';

import { tempLogin } from './helpers';

test.describe('mapper flow', () => {
  test('mapper flow', async ({ browserName, page }) => {
    // Specific for this large test, only run in one browser
    // (playwright.config.ts is configured to run all browsers by default)
    test.skip(browserName !== 'chromium', 'Test only for chromium!');

    await tempLogin(page);

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
    // Use maxDiffPixelRatio to avoid issues with OSM tile loading delay
    expect(await page.locator('canvas').screenshot()).toMatchSnapshot('ready.png', { maxDiffPixelRatio: 0.05 });

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
    // Use maxDiffPixelRatio to avoid issues with OSM tile loading delay
    expect(await page.locator('canvas').screenshot()).toMatchSnapshot('locked-for-mapping.png', {
      maxDiffPixelRatio: 0.05,
    });

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
    // Use maxDiffPixelRatio to avoid issues with OSM tile loading delay
    expect(await page.locator('canvas').screenshot()).toMatchSnapshot('mapped.png', { maxDiffPixelRatio: 0.05 });

    await page.locator('canvas').click({
      position: {
        x: 445,
        y: 95,
      },
    });
    // STATUS: MAPPED
    await page.getByRole('button', { name: 'START VALIDATION' }).click();
    // Wait for redirect to validation page
    await page.waitForTimeout(2000);
    // Click 'Fully Mapped' button on validation page
    await page.getByRole('button', { name: 'MARK AS VALIDATED' }).click();

    await page.getByText('has been updated to VALIDATED').waitFor({ state: 'visible' });
    await expect(page.getByText('has been updated to VALIDATED')).toBeVisible();

    // wait for map to render before continuing
    await page.waitForTimeout(4000);
    // Use maxDiffPixelRatio to avoid issues with OSM tile loading delay
    expect(await page.locator('canvas').screenshot()).toMatchSnapshot('validated.png', { maxDiffPixelRatio: 0.05 });
    await page.locator('canvas').click({
      position: {
        x: 445,
        y: 95,
      },
    });
    await expect(page.getByText('Status: VALIDATED')).toBeVisible();
  });

  test('comment section', async ({ browserName, page }) => {
    // Specific for this large test, only run in one browser
    // (playwright.config.ts is configured to run all browsers by default)
    test.skip(browserName !== 'chromium', 'Test only for chromium!');

    await tempLogin(page);

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
