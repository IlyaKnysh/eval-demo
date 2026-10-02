package com.acme.crm.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;

/**
 * Page object for the Invoice modification screen.
 */
public class InvoiceModifyPage extends BasePage {

    private final By nameField = By.id("invoiceRefInput");
    private final By statusDropdown = By.id("ext-comp-5033");
    private final By emailField = By.name("billingEmail");
    private final By saveButton = By.cssSelector(".crm-form-actions .btn-save");
    private final By activeCheckbox = By.cssSelector(".invoice-modify-panel .active-checkbox");

    public InvoiceModifyPage(WebDriver driver) {
        super(driver);
    }

    public void verifyFieldIsEditableAndEnabled() {
        WebElement field = driver.findElement(nameField);
        if (!field.isEnabled()) {
            throw new AssertionError("Name field is not editable/enabled on Invoice Modify page");
        }
    }

    public void enterName(String name) {
        WebElement field = driver.findElement(nameField);
        field.clear();
        field.sendKeys(name);
    }

    public void selectStatus(String status) {
        selectDropdownByVisibleText(statusDropdown, status);
    }

    public void enterEmail(String email) {
        type(emailField, email);
    }

    public void clickSave() {
        click(saveButton);
    }

    public void toggleActive() {
        click(activeCheckbox);
    }
}
