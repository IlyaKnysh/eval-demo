import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';
import { BasePage } from '@core/BasePage';
import { OrderListPage } from '@pages/OrderListPage';
import { UserListPage } from '@pages/UserListPage';

/**
 * Landing page after login. Acts as a navigation hub — each method
 * returns the next typed page object rather than exposing raw locators.
 */
export class DashboardPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  private get ordersNavLink() {
    return this.page.getByRole('link', { name: 'Orders' });
  }

  private get usersNavLink() {
    return this.page.getByRole('link', { name: 'Users' });
  }

  private get welcomeBanner() {
    return this.page.getByTestId('dashboard-welcome');
  }

  async expectWelcomeVisible(): Promise<void> {
    await expect(this.welcomeBanner).toBeVisible();
  }

  async goToOrders(): Promise<OrderListPage> {
    await this.ordersNavLink.click();
    const listPage = new OrderListPage(this.page);
    await listPage.waitForLoad();
    return listPage;
  }

  async goToUsers(): Promise<UserListPage> {
    await this.usersNavLink.click();
    const listPage = new UserListPage(this.page);
    await listPage.waitForLoad();
    return listPage;
  }
}
