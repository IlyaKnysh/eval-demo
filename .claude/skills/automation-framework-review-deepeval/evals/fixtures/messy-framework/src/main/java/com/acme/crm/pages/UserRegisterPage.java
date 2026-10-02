package com.acme.crm.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

public class UserRegisterPage extends BasePage {

    private final By firstNameField = By.xpath("//div[2]/div[1]/form/div[1]/input");
    private final By lastNameField = By.xpath("//div[2]/div[1]/form/div[2]/input");
    private final By emailField = By.name("email");
    private final By phoneField = By.name("phone");
    private final By roleDropdown = By.id("ext-comp-4108");
    private final By departmentDropdown = By.id("ext-comp-4109");
    private final By addressField = By.cssSelector(".register-form .address-field");
    private final By cityField = By.cssSelector(".register-form .city-field");
    private final By zipField = By.cssSelector(".register-form .zip-field");
    private final By registerButton = By.cssSelector(".register-form-actions .btn-register");
    private final By successMessage = By.cssSelector(".register-success-message");

    public UserRegisterPage(WebDriver driver) {
        super(driver);
    }

    public void enterFirstName(String v) {
        type(firstNameField, v);
    }

    public void enterLastName(String v) {
        type(lastNameField, v);
    }

    public void enterEmail(String v) {
        type(emailField, v);
    }

    public void enterPhone(String v) {
        type(phoneField, v);
    }

    public void selectRole(String v) {
        selectDropdownByVisibleText(roleDropdown, v);
    }

    public void selectDepartment(String v) {
        selectDropdownByVisibleText(departmentDropdown, v);
    }

    public void enterAddress(String v) {
        type(addressField, v);
    }

    public void enterCity(String v) {
        type(cityField, v);
    }

    public void enterZip(String v) {
        type(zipField, v);
    }

    public void submitRegistration() {
        click(registerButton);
        try {
            Thread.sleep(2000);
        } catch (InterruptedException e) {
        }
    }

    public boolean isSuccessMessageShown() {
        return isElementPresentNow(successMessage);
    }
}
