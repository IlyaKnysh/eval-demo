import { test } from '@core/fixtures';
import { createOrder } from '@flows/orderFlows';
import { buildOrder, buildMultiItemOrder } from '@factories/orderFactory';

test.describe('Order creation', () => {
  test(
    'creates a single-item order and shows it in the grid',
    { tag: '@smoke' },
    async ({ adminSession, orderListPage, createdRecords }) => {
      // Arrange
      const order = buildOrder();

      // Act
      createdRecords.order(order.customerEmail);
      await createOrder(adminSession, order);

      // Assert
      await orderListPage.expectGridVisible();
      await orderListPage.expectRowWithCustomer(order.customerName);
    },
  );

  test('creates a multi-item order and shows it in the grid', async ({ adminSession, orderListPage, createdRecords }) => {
    const order = buildMultiItemOrder();

    createdRecords.order(order.customerEmail);
    await createOrder(adminSession, order);

    await orderListPage.expectRowWithCustomer(order.customerName);
  });

  test('creates an order with a custom initial status', async ({ adminSession, orderListPage, createdRecords }) => {
    const order = buildOrder({ status: 'processing' });

    createdRecords.order(order.customerEmail);
    await createOrder(adminSession, order);

    await orderListPage.expectRowWithCustomer(order.customerName);
  });

  test('supports adding custom notes to a new order', async ({ adminSession, orderListPage, createdRecords }) => {
    const order = buildOrder({ notes: 'Customer requested gift wrap.' });

    createdRecords.order(order.customerEmail);
    await createOrder(adminSession, order);

    await orderListPage.expectRowWithCustomer(order.customerName);
  });
});
