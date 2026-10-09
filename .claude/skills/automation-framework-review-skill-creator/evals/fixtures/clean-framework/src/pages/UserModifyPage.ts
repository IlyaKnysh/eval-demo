import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';
import { BasePage } from '@core/BasePage';
import { EntityModifyPanel } from '@core/EntityModifyPanel';
import type { Role, User } from '@domain/domain';

/**
 * Page object for the user invite/edit slide-over. Shares generic panel
 * behavior with OrderModifyPage via EntityModifyPanel instead of
 * duplicating save/cancel/toast logic.
 */
export class UserModifyPage extends BasePage {
  private readonly panel: EntityModifyPanel;

  constructor(page: Page) {
    super(page);
    this.panel = new EntityModifyPanel(page, 'user-modify-panel');
  }

  async waitForOpen(): Promise<void> {
    await this.panel.waitForOpen();
  }

  async fillEmail(email: string): Promise<this> {
    await this.panel.fillField('Email address', email);
    return this;
  }

  async fillDisplayName(displayName: string): Promise<this> {
    await this.panel.fillField('Display name', displayName);
    return this;
  }

  async setRole(role: Role): Promise<this> {
    await this.panel.selectField('Role', role);
    return this;
  }

  async fillFromUserData(user: User): Promise<this> {
    await this.fillEmail(user.email);
    await this.fillDisplayName(user.displayName);
    await this.setRole(user.role);
    return this;
  }

  async save(): Promise<void> {
    await this.panel.save();
  }

  async cancel(): Promise<void> {
    await this.panel.cancel();
  }

  async expectRoleFieldValue(role: Role): Promise<void> {
    await this.panel.expectFieldValue('Role', role);
  }
}
