import type { OrderData, OrderLineItem, OrderStatus } from '@domain/domain';

let sequence = 0;

/**
 * Returns a suffix unique across parallel workers. `fullyParallel: true` runs
 * specs in separate worker processes, so a per-process counter plus Date.now()
 * can collide when two workers tick in the same millisecond; the worker index
 * and a random block make the value unique per process as well as within one.
 */
function nextSuffix(): string {
  sequence += 1;
  const worker = process.env.TEST_WORKER_INDEX ?? '0';
  const entropy = Math.random().toString(36).slice(2, 8);
  return `${worker}-${Date.now()}-${sequence}-${entropy}`;
}

function defaultLineItem(suffix: string): OrderLineItem {
  return {
    sku: `SKU-${suffix}`,
    description: 'Wireless Mouse',
    quantity: 1,
    unitPriceCents: 2499,
  };
}

/**
 * Builder-style factory for Order entities — the single source of truth
 * for what a "test order" looks like. Every order-related test composes
 * its data through this builder rather than repeating giant object
 * literals inline.
 */
export class OrderBuilder {
  private order: OrderData;

  constructor() {
    const suffix = nextSuffix();
    this.order = {
      customerEmail: `customer.${suffix}@example.com`,
      customerName: `Test Customer ${suffix}`,
      status: 'pending',
      items: [defaultLineItem(suffix)],
    };
  }

  withStatus(status: OrderStatus): this {
    this.order.status = status;
    return this;
  }

  withCustomer(name: string, email: string): this {
    this.order.customerName = name;
    this.order.customerEmail = email;
    return this;
  }

  withItems(items: OrderLineItem[]): this {
    this.order.items = items;
    return this;
  }

  addItem(item: OrderLineItem): this {
    this.order.items.push(item);
    return this;
  }

  withNotes(notes: string): this {
    this.order.notes = notes;
    return this;
  }

  build(): OrderData {
    return { ...this.order, items: [...this.order.items] };
  }
}

export function buildOrder(overrides: Partial<OrderData> = {}): OrderData {
  const builder = new OrderBuilder();
  const base = builder.build();
  return { ...base, ...overrides };
}

/** A multi-line order, used by tests that exercise order totals/line-item rendering. */
export function buildMultiItemOrder(): OrderData {
  const suffix = nextSuffix();
  return new OrderBuilder()
    .withItems([
      { sku: `SKU-A-${suffix}`, description: 'Wireless Mouse', quantity: 2, unitPriceCents: 2499 },
      { sku: `SKU-B-${suffix}`, description: 'USB-C Hub', quantity: 1, unitPriceCents: 3999 },
    ])
    .build();
}
