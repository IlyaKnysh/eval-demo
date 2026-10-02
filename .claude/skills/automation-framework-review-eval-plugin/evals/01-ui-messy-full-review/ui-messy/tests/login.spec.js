const { test, expect } = require('@playwright/test');
const { LoginPage } = require('../src/pages/LoginPage');

test('user can log in', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto('/login');
  await loginPage.login('user@example.com', 'password123');
  await expect(page.locator('.welcome-banner')).toBeVisible();
});
