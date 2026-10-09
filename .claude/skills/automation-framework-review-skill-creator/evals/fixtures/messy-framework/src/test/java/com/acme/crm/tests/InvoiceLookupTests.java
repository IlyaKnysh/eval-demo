package com.acme.crm.tests;

import com.acme.crm.pages.LoginPage;
import com.acme.crm.pages.DashboardPage;
import com.acme.crm.pages.OrderCreatePage;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

public class InvoiceLookupTests {

    private WebDriver driver;
    private LoginPage loginPage;
    private DashboardPage dashboardPage;
    private OrderCreatePage orderCreatePage;

    @BeforeClass
    public void setUp() {
        driver = new ChromeDriver();
        loginPage = new LoginPage(driver);
        dashboardPage = new DashboardPage(driver);
        orderCreatePage = new OrderCreatePage(driver);
        driver.get("https://crm-admin.acmecorp.com/login");
        loginPage.loginAsAdmin();
    }

    @Test
    public void testCreateOrderThenLookUpInvoice() {
        dashboardPage.openOrdersMenu();
        orderCreatePage.enterCustomerName("Emily Turner");
        orderCreatePage.enterCustomerEmail("emily.turner@example.com");
        orderCreatePage.selectProduct("Widget Standard");
        orderCreatePage.enterQuantity("3");
        orderCreatePage.submit();

        String orderId = orderCreatePage.getConfirmationOrderId();
        Assert.assertNotNull(orderId, "Order ID should exist before invoice lookup");

        driver.get("https://crm-admin.acmecorp.com/invoices?orderId=" + orderId);
        WebElement invoiceRow = driver.findElement(By.xpath("//div[4]/div[1]/table/tbody/tr[1]/td[2]"));
        String invoiceText = invoiceRow.getText();
        Assert.assertTrue(invoiceText.length() > 0, "Invoice row text should not be empty");
    }

    @Test
    public void testInvoiceGridLoadsWithoutError() {
        driver.get("https://crm-admin.acmecorp.com/invoices");
        WebElement grid = driver.findElement(By.id("invoiceGridContainer"));
        grid.isDisplayed();
    }

    @AfterClass
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }
}
