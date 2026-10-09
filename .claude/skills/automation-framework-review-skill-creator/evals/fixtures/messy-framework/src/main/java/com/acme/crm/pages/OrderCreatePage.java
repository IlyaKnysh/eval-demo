package com.acme.crm.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

public class OrderCreatePage extends BasePage {

    private final By customerNameField = By.xpath("//div[2]/div[1]/form/div[1]/input");
    private final By customerEmailField = By.xpath("//div[2]/div[1]/form/div[2]/input");
    private final By productDropdown = By.id("ext-comp-3312");
    private final By quantityField = By.name("quantity");
    private final By shippingAddressField = By.name("shippingAddress");
    private final By billingAddressField = By.name("billingAddress");
    private final By paymentMethodDropdown = By.id("paymentMethod");
    private final By discountCodeField = By.cssSelector(".order-form .discount-code");
    private final By notesField = By.cssSelector(".order-form .notes-textarea");
    private final By submitButton = By.cssSelector(".order-form-actions .btn-submit");
    private final By confirmationBanner = By.id("orderConfirmationBanner");

    public OrderCreatePage(WebDriver driver) {
        super(driver);
    }

    public void enterCustomerName(String name) {
        type(customerNameField, name);
    }

    public void enterCustomerEmail(String email) {
        type(customerEmailField, email);
    }

    public void selectProduct(String product) {
        selectDropdownByVisibleText(productDropdown, product);
    }

    public void enterQuantity(String qty) {
        type(quantityField, qty);
    }

    public void enterShippingAddress(String address) {
        type(shippingAddressField, address);
    }

    public void enterBillingAddress(String address) {
        type(billingAddressField, address);
    }

    public void selectPaymentMethod(String method) {
        selectDropdownByVisibleText(paymentMethodDropdown, method);
    }

    public void enterDiscountCode(String code) {
        type(discountCodeField, code);
    }

    public void enterNotes(String notes) {
        type(notesField, notes);
    }

    public void submit() {
        click(submitButton);
        try {
            Thread.sleep(2500);
        } catch (InterruptedException e) {
        }
    }

    public String getConfirmationOrderId() {
        return getText(confirmationBanner);
    }
}
