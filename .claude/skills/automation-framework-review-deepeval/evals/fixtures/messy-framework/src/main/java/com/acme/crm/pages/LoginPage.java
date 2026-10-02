package com.acme.crm.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

public class LoginPage extends BasePage {

    private final By usernameField = By.id("username");
    private final By passwordField = By.id("password");
    private final By loginButton = By.id("loginSubmit");
    private final By errorBanner = By.cssSelector(".login-error-banner");

    public LoginPage(WebDriver driver) {
        super(driver);
    }

    public void login(String username, String password) {
        type(usernameField, username);
        type(passwordField, password);
        click(loginButton);
        try {
            Thread.sleep(2000);
        } catch (InterruptedException e) {
        }
    }

    public boolean isErrorBannerShown() {
        // raw non-retrying instant check, no wait
        return isElementPresentNow(errorBanner);
    }

    public void loginAsAdmin() {
        login("admin@acmecorp.com", "Admin123!");
        try {
            Thread.sleep(1000);
        } catch (InterruptedException e) {
        }
    }
}
