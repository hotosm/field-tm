import { test as setup } from '@playwright/test';
import path from 'path';

const authFile = path.join(__dirname, './.auth/user.json');

setup.skip('authenticate', async ({ browserName, page }) => {
  // Note here we only run in chromium, to avoid running this setup step
  // for Firefox and Webkit.
  // This is because Webkit does not respect 'secure' cookies on http contexts.
  // For this to work we would need to configure https for testing
  // https://github.com/hotosm/field-tm/pull/1920
  setup.skip(browserName !== 'chromium', 'Test only for chromium!');

  // Note this sets a token so we can proceed, but the login will be
  // overwritten by svcfmtm localadmin user (as DEBUG=True)
  await page.goto('/playwright-temp-login');

  // Now check we are signed in as localadmin
  await page.waitForSelector('text=localadmin');

  // Save authentication state
  await page.context().storageState({ path: authFile });
});
