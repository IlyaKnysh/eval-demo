import { test } from '@core/fixtures';
import type { DashboardPage } from '@pages/DashboardPage';
import type { OrderData, OrderStatus } from '@domain/domain';
import { withContext } from '@utils/errors';

/**
 * Business-step layer for order-related actions. Tests call these
 * composed, action-verb-phrase functions instead of chaining page-object
 * calls directly, and instead of duplicating the same multi-step
 * sequence inline in every test.
 */

/**
 * Creates a new order from the dashboard and returns to the order list
 * once the save has completed.
 */
export async function createOrder(dashboard: DashboardPage, orderData: OrderData): Promise<void> {
  await withContext(`Creating order for ${orderData.customerName}`, async () => {
    await test.step(`Create order for ${orderData.customerName}`, async () => {
      const listPage = await dashboard.goToOrders();
      const modifyPage = await listPage.openNewOrderPanel();
      await modifyPage.fillFromOrderData(orderData);
      await modifyPage.save();
    });
  });
}

/**
 * Locates an existing order by customer name and updates its status.
 */
export async function updateOrderStatus(
  dashboard: DashboardPage,
  customerName: string,
  status: OrderStatus,
): Promise<void> {
  await withContext(`Updating order status for ${customerName}`, async () => {
    await test.step(`Update order status to "${status}" for ${customerName}`, async () => {
      const listPage = await dashboard.goToOrders();
      const modifyPage = await listPage.openOrderByCustomer(customerName);
      await modifyPage.setStatus(status);
      await modifyPage.save();
    });
  });
}
