/**
 * Shared domain types used consistently across factories, page objects,
 * flows and tests. Keeping a single typed representation for Users/Orders
 * avoids ad-hoc shapes and raw string credentials being passed around.
 */

export type Role = 'admin' | 'standard' | 'read-only';

export interface User {
  email: string;
  password: string;
  displayName: string;
  role: Role;
}

export type OrderStatus = 'pending' | 'processing' | 'shipped' | 'cancelled';

export interface OrderLineItem {
  sku: string;
  description: string;
  quantity: number;
  unitPriceCents: number;
}

export interface OrderData {
  customerEmail: string;
  customerName: string;
  status: OrderStatus;
  items: OrderLineItem[];
  notes?: string;
}
