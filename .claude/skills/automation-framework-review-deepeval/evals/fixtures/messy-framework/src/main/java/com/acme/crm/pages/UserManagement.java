package com.acme.crm.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;

/**
 * Handles the User list/grid screen.
 */
public class UserManagement extends BasePage {

    private final By userRow = By.xpath("//div[2]/div[4]/table/tbody/tr[2]/td[1]");
    private final By searchBox = By.id("userSearchInput");
    private final By addUserButton = By.cssSelector(".user-grid-toolbar .btn-add");

    public UserManagement(WebDriver driver) {
        super(driver);
    }

    public void searchUser(String term) {
        type(searchBox, term);
    }

    public void clickAddUser() {
        click(addUserButton);
    }

    public WebElement getFirstResultRow() {
        return driver.findElement(userRow);
    }
}
