import { test } from '@core/fixtures';
import { loginAsUser, attemptInvalidLogin } from '@flows/authFlows';
import { adminUser, standardUser } from '@factories/userFactory';

test.describe('Login', () => {
  test('admin can log in and reach the dashboard', { tag: '@smoke' }, async ({ page }) => {
    // Arrange
    const user = adminUser();

    // Act
    const dashboard = await loginAsUser(page, user);

    // Assert
    await dashboard.expectWelcomeVisible();
  });

  test('standard agent can log in and reach the dashboard', async ({ page }) => {
    const user = standardUser();

    const dashboard = await loginAsUser(page, user);

    await dashboard.expectWelcomeVisible();
  });

  test('invalid credentials show an error and do not navigate away', { tag: '@smoke' }, async ({ page }) => {
    const loginPage = await attemptInvalidLogin(page, 'nobody@example.com', 'wrong-password');

    await loginPage.expectLoginError('Invalid email or password.');
  });
});
