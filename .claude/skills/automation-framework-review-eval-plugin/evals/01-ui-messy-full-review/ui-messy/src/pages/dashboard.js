const { BasePage } = require('./BasePage');

class Dashboard extends BasePage {
  constructor(page) {
    super(page);
    this.createWidgetButton = page.locator('xpath=//div[3]/div[1]/button[2]');
    this.widgetNameInput = page.locator('#widget-name');
    this.saveButton = page.locator('.save-btn');
  }

  async createWidget(name) {
    await this.createWidgetButton.click();
    await this.page.waitForTimeout(800);
    await this.widgetNameInput.fill(name);
    await this.saveButton.click();
    await this.page.waitForTimeout(1200);
  }
}

module.exports = { Dashboard };
