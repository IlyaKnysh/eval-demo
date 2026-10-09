package com.acme.crm.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;

import java.util.List;

/**
 * Handles the Order list/grid screen.
 */
public class OrderHandler extends BasePage {

    private final By orderRows = By.cssSelector(".order-grid-table .order-row");
    private final By filterDropdown = By.id("ext-comp-1188");
    private final By exportButton = By.cssSelector(".order-grid-toolbar .btn-export");

    public OrderHandler(WebDriver driver) {
        super(driver);
    }

    public void filterByStatus(String status) {
        selectDropdownByVisibleText(filterDropdown, status);
    }

    public void clickExport() {
        click(exportButton);
        try {
            Thread.sleep(4000);
        } catch (InterruptedException e) {
            log("Interrupted while waiting for export: " + e.getMessage());
        }
    }

    public List<WebElement> getAllOrderRows() {
        return driver.findElements(orderRows);
    }
}
