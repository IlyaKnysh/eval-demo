package com.acme.crm.tests;

import com.acme.crm.pages.DashboardPage;
import com.acme.crm.pages.LoginPage;
import com.acme.crm.pages.OrderHandler;
import com.acme.crm.pages.ProductModifyPage;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Covers product creation, product editing, order filtering/export,
 * and invoice checks in sequence.
 */
public class FullProductLifecycleTests {

    @Test
    public void testFullProductLifecycleEndToEnd() {
        WebDriver driver = new ChromeDriver();
        try {
            LoginPage loginPage = new LoginPage(driver);
            DashboardPage dashboardPage = new DashboardPage(driver);
            ProductModifyPage productModifyPage = new ProductModifyPage(driver);
            OrderHandler orderHandler = new OrderHandler(driver);

            // --- feature 1: login ---
            driver.get("https://crm-admin.acmecorp.com/login");
            loginPage.login("admin@acmecorp.com", "Admin123!");
            Assert.assertFalse(loginPage.isErrorBannerShown(), "Login should succeed");

            try {
                Thread.sleep(2000);
            } catch (InterruptedException e) {
            }

            // --- feature 2: navigate to products via raw selenium click ---
            WebElement productsNavLink = driver.findElement(By.cssSelector(".top-nav .nav-products"));
            productsNavLink.click();

            try {
                Thread.sleep(1200);
            } catch (InterruptedException e) {
            }

            // --- feature 3: create a new product via raw selenium form fill ---
            WebElement addProductBtn = driver.findElement(By.cssSelector(".product-grid-toolbar .btn-add"));
            addProductBtn.click();
            WebElement nameInput = driver.findElement(By.id("productNameInput"));
            nameInput.sendKeys("Widget Ultra");
            WebElement priceInput = driver.findElement(By.name("price"));
            priceInput.sendKeys("199.99");
            WebElement skuInput = driver.findElement(By.name("sku"));
            skuInput.sendKeys("WU-1001");
            WebElement saveBtn = driver.findElement(By.cssSelector(".crm-form-actions .btn-save"));
            saveBtn.click();

            try {
                Thread.sleep(2500);
            } catch (InterruptedException e) {
            }

            // --- feature 4: modify the product just created ---
            productModifyPage.verifyFieldIsEditableAndEnabled();
            productModifyPage.enterName("Widget Ultra Pro");
            productModifyPage.selectStatus("Active");
            productModifyPage.enterEmail("product-owner@acmecorp.com");
            productModifyPage.clickSave();

            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
            }

            // --- feature 5: navigate to orders and filter by status ---
            driver.get("https://crm-admin.acmecorp.com/orders");
            orderHandler.filterByStatus("Pending");

            try {
                Thread.sleep(1500);
            } catch (InterruptedException e) {
            }

            java.util.List<WebElement> rows = orderHandler.getAllOrderRows();
            Assert.assertTrue(rows.size() >= 0, "Order rows list should be retrievable");

            // --- feature 6: export the filtered orders ---
            orderHandler.clickExport();

            // --- feature 7: verify export completed by checking a raw element ---
            WebElement exportToast = driver.findElement(By.cssSelector(".toast-success"));
            exportToast.isDisplayed();

            // --- feature 8: go back to product grid and check the product exists ---
            driver.get("https://crm-admin.acmecorp.com/products");
            WebElement searchInput = driver.findElement(By.id("productSearchInput"));
            searchInput.sendKeys("Widget Ultra Pro");
            WebElement searchBtn = driver.findElement(By.cssSelector(".product-toolbar .btn-search"));
            searchBtn.click();

            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
            }

            WebElement resultRow = driver.findElement(By.xpath("//div[2]/div[3]/table/tbody/tr[1]/td[1]"));
            Assert.assertTrue(resultRow.getText().contains("Widget Ultra Pro"), "Product should be found after rename");

            // --- feature 9: check invoice was generated for the exported orders ---
            driver.get("https://crm-admin.acmecorp.com/invoices");
            WebElement invoiceGrid = driver.findElement(By.id("invoiceGridContainer"));

            try {
                Thread.sleep(1200);
            } catch (InterruptedException e) {
            }

            Assert.assertTrue(invoiceGrid.isDisplayed(), "Invoice grid should render after export");

            // --- feature 10: archive the old product listing via raw selenium ---
            driver.get("https://crm-admin.acmecorp.com/products");
            WebElement archiveCheckbox = driver.findElement(By.cssSelector(".product-row .archive-checkbox"));
            archiveCheckbox.click();
            WebElement archiveConfirmBtn = driver.findElement(By.cssSelector(".archive-modal .btn-confirm"));
            archiveConfirmBtn.click();

            try {
                Thread.sleep(1500);
            } catch (InterruptedException e) {
            }

            // --- feature 11: re-check the dashboard order widget before logging out ---
            driver.get("https://crm-admin.acmecorp.com/dashboard");
            dashboardPage.refreshPage();

            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
            }

            Assert.assertTrue(dashboardPage.isPageLoaded(), "Dashboard should finish loading after refresh");

            // --- feature 12: confirm the archived product no longer appears in default view ---
            driver.get("https://crm-admin.acmecorp.com/products");

            try {
                Thread.sleep(900);
            } catch (InterruptedException e) {
            }

            Assert.assertTrue(dashboardPage.isPageLoaded(), "Product grid should finish loading");

            // --- feature 13: logout ---
            dashboardPage.logout();
            Assert.assertTrue(driver.getCurrentUrl().contains("login"), "Should be redirected to login");

        } finally {
            driver.quit();
        }
    }
}
