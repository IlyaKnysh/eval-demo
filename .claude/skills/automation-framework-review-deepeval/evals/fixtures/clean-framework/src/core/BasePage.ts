import type { Page } from '@playwright/test';
import { withContext } from '@utils/errors';

/**
 * Deliberately slim base class: navigation only. No shared assertion
 * helpers, no God-object grab-bag of unrelated methods. Cross-cutting
 * setup (authenticated page, seeded data, etc.) is handled by Playwright
 * fixtures in fixtures.ts, not by inheritance chains.
 */
export abstract class BasePage {
  constructor(protected readonly page: Page) {}

  async goto(path: string): Promise<void> {
    await withContext(`Navigating to ${path}`, () => this.page.goto(path));
  }

  async waitForLoad(): Promise<void> {
    await this.page.waitForLoadState('networkidle');
  }
}
