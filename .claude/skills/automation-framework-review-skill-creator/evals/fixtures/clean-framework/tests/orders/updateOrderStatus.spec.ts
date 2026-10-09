import { test } from '@core/fixtures';
import { createOrder, updateOrderStatus } from '@flows/orderFlows';
import { buildOrder } from '@factories/orderFactory';

test.describe('Order status updates', () => {
  test(
    'transitions a pending order to processing',
    { tag: '@smoke' },
    async ({ adminSession, orderListPage, createdRecords }) => {
      const order = buildOrder({ status: 'pending' });
      createdRecords.order(order.customerEmail);
      await createOrder(adminSession, order);

      await updateOrderStatus(adminSession, order.customerName, 'processing');

      const modifyPage = await orderListPage.openOrderByCustomer(order.customerName);
      await modifyPage.expectStatusFieldValue('processing');
    },
  );

  test('transitions an order to shipped', async ({ adminSession, orderListPage, createdRecords }) => {
    const order = buildOrder({ status: 'processing' });
    createdRecords.order(order.customerEmail);
    await createOrder(adminSession, order);

    await updateOrderStatus(adminSession, order.customerName, 'shipped');

    const modifyPage = await orderListPage.openOrderByCustomer(order.customerName);
    await modifyPage.expectStatusFieldValue('shipped');
  });

  test('cancels a pending order', async ({ adminSession, orderListPage, createdRecords }) => {
    const order = buildOrder({ status: 'pending' });
    createdRecords.order(order.customerEmail);
    await createOrder(adminSession, order);

    await updateOrderStatus(adminSession, order.customerName, 'cancelled');

    const modifyPage = await orderListPage.openOrderByCustomer(order.customerName);
    await modifyPage.expectStatusFieldValue('cancelled');
  });
});
