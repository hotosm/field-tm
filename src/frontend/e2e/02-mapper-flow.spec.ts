// This file tests the mapper workflow, including changing task status
// to locked, mapped, validated, and then commenting on the task.

import { test, expect } from '@playwright/test';

import { openTestProject } from './helpers';

test.describe('mapper flow', () => {
  test('task actions', async ({ browserName, page }) => {
    // Specific for this large test, only run in one browser
    // (playwright.config.ts is configured to run all browsers by default)
    test.skip(browserName !== 'chromium', 'Test only for chromium!');

    // 1. Click on task area on map
    await openTestProject(page);
    await page.locator('canvas').click({
      position: {
        x: 445,
        y: 95,
      },
    });
    await expect(page.getByText('Status: UNLOCKED_TO_MAP')).toBeVisible();
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

    // 2. Lock task for mapping
    await expect(page.getByTestId('StartMapping')).toBeVisible();
    await page.getByTestId('StartMapping').click();
    await page.waitForSelector('div:has-text("updated to LOCKED_FOR_MAPPING"):nth-of-type(1)');
    await expect(
      page
        .locator('div')
        .filter({ hasText: /updated to LOCKED_FOR_MAPPING/ })
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

    // 3. Mark task as fully mapped
    await page.getByRole('button', { name: 'MARK AS FULLY MAPPED' }).click();
    // Required again for the confirmation dialog (0/4 features mapped)
    await page.getByRole('button', { name: 'MARK AS FULLY MAPPED' }).click();
    await page.waitForSelector('div:has-text("has been updated to UNLOCKED_TO_VALIDATE"):nth-of-type(1)');
    await expect(
      page
        .locator('div')
        .filter({ hasText: /has been updated to UNLOCKED_TO_VALIDATE/ })
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

    // 4. Mark task as validated
    await page.getByRole('button', { name: 'START VALIDATION' }).click();
    // Wait for redirect to validation page
    await page.waitForTimeout(2000);
    // Click 'Fully Mapped' button on validation page
    await page.getByRole('button', { name: 'MARK AS VALIDATED' }).click();

    await page.getByText('has been updated to UNLOCKED_DONE').waitFor({ state: 'visible' });
    await expect(page.getByText('has been updated to UNLOCKED_DONE')).toBeVisible();

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
    await expect(page.getByText('Status: UNLOCKED_DONE')).toBeVisible();
  });

  test('open feature (Entity) in ODK', async ({ browserName, page }) => {
    // Specific for this large test, only run in one browser
    // (playwright.config.ts is configured to run all browsers by default)
    test.skip(browserName !== 'chromium', 'Test only for chromium!');

    // 1. Click on task area on map
    // click on task & assert task popup visibility
    await openTestProject(page);
    await page.locator('canvas').click({
      position: {
        x: 388,
        y: 220,
      },
    });
    await expect(page.getByText('Status: UNLOCKED_TO_MAP')).toBeVisible();
    await expect(page.getByTestId('StartMapping')).toBeVisible();

    // 2. Click on a specific feature / Entity within a task
    // assert feature popup visibility
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
    // Check popup shows because we are not on a mobile device
    await expect(
      page.getByRole('alert').locator('div').filter({ hasText: 'Requires a mobile phone with ODK collect' }),
    ).toBeVisible();

    // 3. Validate feature status updated / locked
    // check if task status is updated to locked_for_mapping on entity map
    await page.waitForSelector('div:has-text("has been updated to LOCKED_FOR_MAPPING"):nth-of-type(1)');
    await expect(
      page
        .locator('div')
        .filter({ hasText: /has been updated to LOCKED_FOR_MAPPING/ })
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

  test('add comment', async ({ browserName, page }) => {
    // Specific for this large test, only run in one browser
    // (playwright.config.ts is configured to run all browsers by default)
    test.skip(browserName !== 'chromium', 'Test only for chromium!');

    await openTestProject(page);
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
