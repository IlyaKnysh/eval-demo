import { test as base } from '@playwright/test';
import type { Page } from '@playwright/test';
import { LoginPage } from '@pages/LoginPage';
import { DashboardPage } from '@pages/DashboardPage';
import { OrderListPage } from '@pages/OrderListPage';
import { UserListPage } from '@pages/UserListPage';
import { adminUser } from '@factories/userFactory';
import type { User } from '@domain/domain';
import { withContext } from '@utils/errors';

/**
 * Framework-wide fixture composition. This is the DI mechanism for the
 * suite: page objects and authenticated sessions are provided via
 * Playwright's `test.extend`, not via a shared base-class hierarchy.
 *
 * Each fixture creates fresh state per test — there is no shared mutable
 * state carried between tests.
 */
type Fixtures = {
  loginPage: LoginPage;
  orderListPage: OrderListPage;
  userListPage: UserListPage;
  adminSession: DashboardPage;
  createdRecords: CreatedRecords;
};

/**
 * Per-test cleanup ledger. A test registers anything it creates against the
 * shared staging environment; the fixture deletes those records during
 * teardown so runs don't leave orphaned data behind for the next one.
 */
export type CreatedRecords = {
  /** Register an order for teardown, keyed by the customer email it was created for. */
  order(customerEmail: string): void;
  /** Register a user for teardown, keyed by email. */
  user(email: string): void;
};

export const test = base.extend<Fixtures>({
  loginPage: async ({ page }, use) => {
    const loginPage = new LoginPage(page);
    await use(loginPage);
  },

  orderListPage: async ({ page }, use) => {
    await use(new OrderListPage(page));
  },

  userListPage: async ({ page }, use) => {
    await use(new UserListPage(page));
  },

  // Pre-authenticated dashboard as an admin. Each test gets its own fresh
  // login rather than reusing storage state mutated by a previous test.
  adminSession: async ({ page }, use) => {
    const dashboard = await loginAs(page, adminUser());
    await use(dashboard);
  },

  createdRecords: async ({ page }, use) => {
    const orders: string[] = [];
    const users: string[] = [];

    await use({
      order: (customerEmail: string) => orders.push(customerEmail),
      user: (email: string) => users.push(email),
    });

    // Teardown runs even when the test body failed, so a mid-test failure
    // still cleans up whatever it managed to create.
    for (const customerEmail of orders.reverse()) {
      await deleteOrder(page, customerEmail);
    }
    for (const email of users.reverse()) {
      await deleteUser(page, email);
    }
  },
});

async function loginAs(page: Page, user: User) {
  const loginPage = new LoginPage(page);
  await loginPage.open();
  return loginPage.loginAs(user);
}

async function deleteOrder(page: Page, customerEmail: string) {
  await withContext(`delete orders for ${customerEmail}`, async () => {
    const response = await page.request.delete(
      `/api/orders?customerEmail=${encodeURIComponent(customerEmail)}`,
    );
    if (!response.ok()) {
      throw new Error(`cleanup returned ${response.status()}`);
    }
  });
}

async function deleteUser(page: Page, email: string) {
  await withContext(`delete user ${email}`, async () => {
    const response = await page.request.delete(
      `/api/users/${encodeURIComponent(email)}`,
    );
    if (!response.ok()) {
      throw new Error(`cleanup returned ${response.status()}`);
    }
  });
}

export { expect } from '@playwright/test';
