import { test } from '@core/fixtures';
import type { Page } from '@playwright/test';
import { LoginPage } from '@pages/LoginPage';
import type { User } from '@domain/domain';
import type { DashboardPage } from '@pages/DashboardPage';
import { withContext } from '@utils/errors';

/** Logs in as the given user from a fresh, unauthenticated page. */
export async function loginAsUser(page: Page, user: User): Promise<DashboardPage> {
  return withContext(`Signing in as ${user.email}`, async () => {
    return test.step(`Sign in as ${user.email}`, async () => {
      const loginPage = new LoginPage(page);
      await loginPage.open();
      return loginPage.loginAs(user);
    });
  });
}

/** Attempts a login expected to fail, and returns the LoginPage for assertions. */
export async function attemptInvalidLogin(page: Page, email: string, password: string): Promise<LoginPage> {
  return withContext(`Attempting invalid login as ${email}`, async () => {
    return test.step(`Attempt invalid login as ${email}`, async () => {
      const loginPage = new LoginPage(page);
      await loginPage.open();
      await loginPage.submitLoginAttempt(email, password);
      return loginPage;
    });
  });
}
