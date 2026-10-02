import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';
import { BasePage } from '@core/BasePage';
import { getUniqueGridRow } from '@utils/gridUtils';
import { OrderModifyPage } from '@pages/OrderModifyPage';

/** Page object for the paginated order grid. */
export class OrderListPage extends BasePage {
  private static readonly GRID_TESTID = 'orders-grid';

  constructor(page: Page) {
    super(page);
  }

  private get grid() {
    return this.page.getByTestId(OrderListPage.GRID_TESTID);
  }

  private get newOrderButton() {
    return this.page.getByRole('button', { name: 'New order' });
  }

  private get searchInput() {
    return this.page.getByLabel('Search orders');
  }

  async expectGridVisible(): Promise<void> {
    await expect(this.grid).toBeVisible();
  }

  async searchFor(term: string): Promise<void> {
    await this.searchInput.fill(term);
    await this.searchInput.press('Enter');
  }

  async expectRowWithCustomer(customerName: string): Promise<void> {
    const row = await getUniqueGridRow(this.page, OrderListPage.GRID_TESTID, customerName);
    await expect(row).toBeVisible();
  }

  async openNewOrderPanel(): Promise<OrderModifyPage> {
    await this.newOrderButton.click();
    const modifyPage = new OrderModifyPage(this.page);
    await modifyPage.waitForOpen();
    return modifyPage;
  }

  async openOrderByCustomer(customerName: string): Promise<OrderModifyPage> {
    const row = await getUniqueGridRow(this.page, OrderListPage.GRID_TESTID, customerName);
    await row.getByRole('button', { name: 'Edit' }).click();
    const modifyPage = new OrderModifyPage(this.page);
    await modifyPage.waitForOpen();
    return modifyPage;
  }
}
