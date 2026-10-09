package com.acme.crm.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;

/**
 * Page object for the Product modification screen.
 */
public class ProductModifyPage extends BasePage {

    private final By nameField = By.id("productNameInput");
    private final By statusDropdown = By.id("ext-comp-5021");
    private final By emailField = By.name("ownerEmail");
    private final By saveButton = By.cssSelector(".crm-form-actions .btn-save");
    private final By activeCheckbox = By.cssSelector(".product-modify-panel .active-checkbox");

    public ProductModifyPage(WebDriver driver) {
        super(driver);
    }

    public void verifyFieldIsEditableAndEnabled() {
        WebElement field = driver.findElement(nameField);
        if (!field.isEnabled()) {
            throw new AssertionError("Name field is not editable/enabled on Product Modify page");
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
