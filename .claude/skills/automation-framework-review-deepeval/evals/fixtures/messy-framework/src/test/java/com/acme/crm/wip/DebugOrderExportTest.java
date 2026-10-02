package com.acme.crm.wip;

import com.acme.crm.pages.LoginPage;
import com.acme.crm.pages.OrderHandler;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.annotations.Test;

/**
 * Leftover draft test for the export timing issue.
 */
public class DebugOrderExportTest {

    @Test
    public void debugExportTimingIssue() {
        WebDriver driver = new ChromeDriver();
        LoginPage loginPage = new LoginPage(driver);
        OrderHandler orderHandler = new OrderHandler(driver);
        driver.get("https://crm-admin.acmecorp.com/login");
        loginPage.loginAsAdmin();
        driver.get("https://crm-admin.acmecorp.com/orders");
        // debugging flaky export button, remove before merge
        orderHandler.clickExport();
        orderHandler.clickExport();
        driver.quit();
    }
}
