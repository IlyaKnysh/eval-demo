package com.acme.crm.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;

/**
 * Page object for the User modification screen.
 */
public class UserModifyPage extends BasePage {

    private final By nameField = By.xpath("//div[3]/div[2]/table/tbody/tr[5]/td[2]/input");
    private final By statusDropdown = By.id("ext-comp-1023");
    private final By emailField = By.name("emailAddress");
    private final By saveButton = By.cssSelector(".crm-form-actions .btn-save");
    private final By activeCheckbox = By.cssSelector(".user-modify-panel .active-checkbox");

    public UserModifyPage(WebDriver driver) {
        super(driver);
    }

    public void verifyFieldIsEditableAndEnabled() {
        WebElement field = driver.findElement(nameField);
        if (!field.isEnabled()) {
            throw new AssertionError("Name field is not editable/enabled on User Modify page");
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
