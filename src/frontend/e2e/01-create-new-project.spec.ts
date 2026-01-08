// This file tests the project creation workflow, using standard inputs
// such as the default XLSForm and an OSM data extract.

import { test, expect } from '@playwright/test';

test.skip('create new project', async ({ browserName, page }) => {
  // Specific for this large test, only run in one browser
  // (playwright.config.ts is configured to run all browsers by default)
  test.skip(browserName !== 'chromium', 'Test only for chromium!');

  await page.goto('/');
  await page.getByRole('button', { name: '+ Create New Project' }).click();
  await page.getByRole('button', { name: 'NEXT' }).click();

  // 1. Project Details Step
  await expect(page.getByText('Project Name is Required.')).toBeVisible();
  await expect(page.getByText('Short Description is Required.', { exact: true })).toBeVisible();
  await expect(page.getByText('Description is Required.', { exact: true })).toBeVisible();
  await expect(page.getByText('Organization is Required.')).toBeVisible();
  await expect(page.getByText('ODK URL is Required.')).toBeVisible();
  await page.locator('#name').click();
  // The project name must be unique when running multiple tests
  const randomId = Math.random() * 10000000000000000;
  await page.locator('#name').fill(`Project Create Playwright ${randomId}`);
  await page.locator('#description').click();
  await page.locator('#description').fill('desc');
  await page.getByRole('combobox').click();
  await page.getByLabel('HOTOSM').click();
  await page.getByRole('button', { name: 'NEXT' }).click();

  // 2. Upload Area Step
  const uploadAOIFileRadio = await page.getByText('Upload File');
  await uploadAOIFileRadio.click();
  await expect(uploadAOIFileRadio).toBeChecked();
  await page.waitForSelector('#file-input');
  await page.locator('#file-input').click();
  const input = page.locator('#data-extract-custom-file');
  // Remove the hidden class from the input element so that playwright can click on it
  await page.evaluate(
    (input) => {
      if (input) input.classList.remove('fmtm-hidden');
    },
    await input.elementHandle(),
  );
  // first adding invalid geojson then valid geojson
  // @ts-ignore
  await page.locator('#data-extract-custom-file').setInputFiles(`${__dirname}/files/invalid-aoi.geojson`);
  await expect(page.getByText('The project area exceeded 200')).toBeVisible();
  await page.locator('#data-extract-custom-file').setInputFiles([]);
  // @ts-ignore
  await page.locator('#data-extract-custom-file').setInputFiles(`${__dirname}/files/valid-aoi.geojson`);
  // Reapply the hidden class to the input element
  await page.evaluate(
    (input) => {
      if (input) input.classList.add('fmtm-hidden');
    },
    await input.elementHandle(),
  );
  await page.getByRole('button', { name: 'NEXT' }).click();

  // 3. Select Category Step
  await page.getByRole('button', { name: 'NEXT' }).click();
  await expect(page.getByText('Survey Type is Required.')).toBeVisible();
  await page.getByRole('combobox').click();
  await page.getByLabel('buildings').click();
  await page.getByRole('button', { name: 'NEXT' }).click();

  // 4. Map Features Step
  const dataExtractRadio = await page.getByText('Fetch data from OSM');
  await dataExtractRadio.click();
  await expect(dataExtractRadio).toBeChecked();
  await page.getByRole('button', { name: 'Fetch OSM Data' }).click();
  await page.getByRole('button', { name: 'NEXT' }).click();

  // 5. Split Tasks Step
  await page.getByText('Task Splitting Algorithm', { exact: true }).click();
  await page.getByRole('spinbutton').click();
  await page.getByRole('spinbutton').fill('3');
  await page.getByRole('button', { name: 'Click to generate task' }).click();
  await page.getByRole('button', { name: 'SUBMIT' }).click();

  const projectCreationSuccessToast = page.getByText('Project Generation Completed. Redirecting...');
  await projectCreationSuccessToast.waitFor({ state: 'visible' });
  await expect(projectCreationSuccessToast).toBeVisible();
});
