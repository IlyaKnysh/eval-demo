import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';
import { BasePage } from '@core/BasePage';
import type { User } from '@domain/domain';
import { withContext } from '@utils/errors';
import { DashboardPage } from '@pages/DashboardPage';

/**
 * Page object for the admin login screen. Public methods return either
 * `this` (for chaining within the same page) or the next typed page
 * object — never a raw Locator.
 */
export class LoginPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  private get emailInput() {
    return this.page.getByLabel('Email address');
  }

  private get passwordInput() {
    return this.page.getByLabel('Password');
  }

  private get signInButton() {
    return this.page.getByRole('button', { name: 'Sign in' });
  }

  private get errorBanner() {
    return this.page.getByRole('alert');
  }

  async open(): Promise<this> {
    await this.goto('/login');
    await expect(this.emailInput).toBeVisible();
    return this;
  }

  /**
   * Single, typed entry point for authenticating as any user in the
   * system. No test bypasses this with a raw credential string.
   */
  async loginAs(user: User): Promise<DashboardPage> {
    return withContext(`Logging in as ${user.email}`, async () => {
      await this.emailInput.fill(user.email);
      await this.passwordInput.fill(user.password);
      await this.signInButton.click();
      const dashboard = new DashboardPage(this.page);
      await dashboard.waitForLoad();
      return dashboard;
    });
  }

  /**
   * Submits the login form without assuming success — used by negative
   * tests that expect to stay on the login page with an error banner.
   * Unlike loginAs(), this does not navigate to DashboardPage.
   */
  async submitLoginAttempt(email: string, password: string): Promise<this> {
    return withContext(`Submitting login attempt for ${email}`, async () => {
      await this.emailInput.fill(email);
      await this.passwordInput.fill(password);
      await this.signInButton.click();
      return this;
    });
  }

  async expectLoginError(message: string): Promise<void> {
    await expect(this.errorBanner).toBeVisible();
    await expect(this.errorBanner).toHaveText(message);
  }
}
