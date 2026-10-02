import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';
import { withContext } from '@utils/errors';

/**
 * Shared logic for the "modify entity" slide-over panel that both the
 * Order and User modify screens use (same underlying UI component in the
 * app). Factored out here so OrderModifyPage and UserModifyPage compose
 * this helper instead of copy-pasting save/cancel/status-toast handling.
 *
 * This is intentionally a small composed helper, not a shared base class,
 * per the framework's fixture-over-inheritance convention.
 */
export class EntityModifyPanel {
  constructor(
    private readonly page: Page,
    private readonly panelTestId: string,
  ) {}

  private get panel() {
    return this.page.getByTestId(this.panelTestId);
  }

  private get saveButton() {
    return this.panel.getByRole('button', { name: 'Save changes' });
  }

  private get cancelButton() {
    return this.panel.getByRole('button', { name: 'Cancel' });
  }

  private get successToast() {
    return this.page.getByRole('status').filter({ hasText: 'Saved successfully' });
  }

  async waitForOpen(): Promise<void> {
    await expect(this.panel).toBeVisible();
  }

  /**
   * Typed field operations. These replace an earlier `fieldByLabel()` that
   * returned the raw Locator: handing a Locator to callers pushed Playwright
   * types out of core into every page object, which CONTRIBUTING.md's
   * layering rule forbids. Keeping the Locator private here means the panel
   * owns how a field is driven, and call sites express intent instead.
   */
  async fillField(label: string, value: string): Promise<void> {
    await this.panel.getByLabel(label).fill(value);
  }

  async selectField(label: string, value: string): Promise<void> {
    await this.panel.getByLabel(label).selectOption(value);
  }

  async expectFieldValue(label: string, value: string): Promise<void> {
    await expect(this.panel.getByLabel(label)).toHaveValue(value);
  }

  async save(): Promise<void> {
    await withContext(`Saving entity panel "${this.panelTestId}"`, async () => {
      await this.saveButton.click();
      await expect(this.successToast).toBeVisible();
      await expect(this.panel).toBeHidden();
    });
  }

  async cancel(): Promise<void> {
    await this.cancelButton.click();
    await expect(this.panel).toBeHidden();
  }
}
