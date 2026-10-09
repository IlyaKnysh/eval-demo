import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';
import { BasePage } from '@core/BasePage';
import { EntityModifyPanel } from '@core/EntityModifyPanel';
import type { OrderData, OrderStatus } from '@domain/domain';

/**
 * Page object for the order create/edit slide-over. Delegates generic
 * panel behavior (save/cancel/toast) to EntityModifyPanel rather than
 * duplicating it — see UserModifyPage for the equivalent pattern.
 */
export class OrderModifyPage extends BasePage {
  private readonly panel: EntityModifyPanel;

  constructor(page: Page) {
    super(page);
    this.panel = new EntityModifyPanel(page, 'order-modify-panel');
  }

  async waitForOpen(): Promise<void> {
    await this.panel.waitForOpen();
  }

  async fillCustomerDetails(customerName: string, customerEmail: string): Promise<this> {
    await this.panel.fillField('Customer name', customerName);
    await this.panel.fillField('Customer email', customerEmail);
    return this;
  }

  async setStatus(status: OrderStatus): Promise<this> {
    await this.panel.selectField('Status', status);
    return this;
  }

  async addLineItem(sku: string, quantity: number): Promise<this> {
    await this.panel.fillField('SKU', sku);
    await this.panel.fillField('Quantity', String(quantity));
    return this;
  }

  async fillFromOrderData(order: OrderData): Promise<this> {
    await this.fillCustomerDetails(order.customerName, order.customerEmail);
    await this.setStatus(order.status);
    for (const item of order.items) {
      await this.addLineItem(item.sku, item.quantity);
    }
    return this;
  }

  async save(): Promise<void> {
    await this.panel.save();
  }

  async cancel(): Promise<void> {
    await this.panel.cancel();
  }

  async expectStatusFieldValue(status: OrderStatus): Promise<void> {
    await this.panel.expectFieldValue('Status', status);
  }
}
