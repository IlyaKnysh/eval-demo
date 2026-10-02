const { test, expect } = require('@playwright/test');
const { LoginPage } = require('../src/pages/LoginPage');
const { Dashboard } = require('../src/pages/dashboard');

test('create a standard widget', async ({ page }) => {
  const loginPage = new LoginPage(page);
  const dashboard = new Dashboard(page);
  await loginPage.goto('/login');
  await loginPage.login('user@example.com', 'password123');
  await dashboard.createWidget('Standard Widget');
  await expect(page.locator('.widget-list')).toContainText('Standard Widget');
});

test('create a widget with raw locator bypass', async ({ page }) => {
  const loginPage = new LoginPage(page);
  const dashboard = new Dashboard(page);
  await loginPage.goto('/login');
  await loginPage.login('user@example.com', 'password123');
  await dashboard.createWidget('Second Widget');
  // bypasses the page object entirely for a quick check
  await page.locator('.widget-list li').last().click();
  await expect(page.locator('.widget-detail-title')).toHaveText('Second Widget');
});
