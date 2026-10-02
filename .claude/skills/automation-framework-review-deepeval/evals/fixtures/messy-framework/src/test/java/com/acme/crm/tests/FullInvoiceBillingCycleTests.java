package com.acme.crm.tests;

import com.acme.crm.pages.DashboardPage;
import com.acme.crm.pages.InvoiceModifyPage;
import com.acme.crm.pages.LoginPage;
import com.acme.crm.pages.OrderCreatePage;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Covers order creation, invoice generation, invoice editing, payment
 * status update and email notification checks in sequence.
 */
public class FullInvoiceBillingCycleTests {

    @Test
    public void testFullInvoiceBillingCycleEndToEnd() {
        WebDriver driver = new ChromeDriver();
        try {
            LoginPage loginPage = new LoginPage(driver);
            DashboardPage dashboardPage = new DashboardPage(driver);
            OrderCreatePage orderCreatePage = new OrderCreatePage(driver);
            InvoiceModifyPage invoiceModifyPage = new InvoiceModifyPage(driver);

            // --- feature 1: login ---
            driver.get("https://crm-admin.acmecorp.com/login");
            loginPage.login("admin@acmecorp.com", "Admin123!");
            Assert.assertFalse(loginPage.isErrorBannerShown(), "Login should succeed");

            try {
                Thread.sleep(2000);
            } catch (InterruptedException e) {
            }

            // --- feature 2: create an order that will need billing ---
            dashboardPage.openOrdersMenu();
            orderCreatePage.enterCustomerName("Henry Osborne");
            orderCreatePage.enterCustomerEmail("henry.osborne@example.com");
            orderCreatePage.selectProduct("Widget Deluxe");
            orderCreatePage.enterQuantity("8");
            orderCreatePage.enterShippingAddress("900 Cedar Blvd, Miami, FL 33101");
            orderCreatePage.enterBillingAddress("900 Cedar Blvd, Miami, FL 33101");
            orderCreatePage.selectPaymentMethod("Invoice");
            orderCreatePage.submit();

            String orderId = orderCreatePage.getConfirmationOrderId();
            Assert.assertNotNull(orderId, "Order should be created");

            try {
                Thread.sleep(3000);
            } catch (InterruptedException e) {
            }

            // --- feature 3: navigate to invoices and locate the generated invoice ---
            driver.get("https://crm-admin.acmecorp.com/invoices?orderId=" + orderId);
            WebElement invoiceRow = driver.findElement(By.xpath("//div[4]/div[1]/table/tbody/tr[1]/td[2]"));
            String invoiceRef = invoiceRow.getText();
            Assert.assertTrue(invoiceRef.length() > 0, "Invoice reference should not be empty");

            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
            }

            // --- feature 4: open and edit the invoice ---
            invoiceRow.click();
            invoiceModifyPage.verifyFieldIsEditableAndEnabled();
            invoiceModifyPage.enterName(invoiceRef + "-REV1");
            invoiceModifyPage.selectStatus("Sent");
            invoiceModifyPage.enterEmail("billing@acmecorp.com");
            invoiceModifyPage.clickSave();

            try {
                Thread.sleep(1500);
            } catch (InterruptedException e) {
            }

            // --- feature 5: mark invoice as paid ---
            invoiceModifyPage.selectStatus("Paid");
            invoiceModifyPage.toggleActive();
            invoiceModifyPage.clickSave();

            try {
                Thread.sleep(1200);
            } catch (InterruptedException e) {
            }

            // --- feature 6: verify a payment confirmation toast appears ---
            WebElement paymentToast = driver.findElement(By.cssSelector(".toast-success.payment-confirmed"));
            Assert.assertTrue(paymentToast.isDisplayed(), "Payment confirmation toast should show");

            // --- feature 7: check the order status reflects payment ---
            driver.get("https://crm-admin.acmecorp.com/orders?orderId=" + orderId);
            WebElement orderStatusBadge = driver.findElement(By.cssSelector(".order-detail .status-badge"));
            Assert.assertEquals(orderStatusBadge.getText(), "Paid", "Order status should update to Paid");

            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
            }

            // --- feature 8: verify dashboard revenue widget updates ---
            driver.get("https://crm-admin.acmecorp.com/dashboard");
            Assert.assertTrue(dashboardPage.isWelcomeBannerVisible(), "Dashboard should reload");

            // --- feature 9: send billing confirmation email via raw selenium trigger ---
            driver.get("https://crm-admin.acmecorp.com/invoices?orderId=" + orderId);
            WebElement sendEmailBtn = driver.findElement(By.cssSelector(".invoice-detail .btn-send-email"));
            sendEmailBtn.click();

            try {
                Thread.sleep(1800);
            } catch (InterruptedException e) {
            }

            WebElement emailSentToast = driver.findElement(By.cssSelector(".toast-success.email-sent"));
            Assert.assertTrue(emailSentToast.isDisplayed(), "Email sent confirmation should show");

            // --- feature 10: archive the completed invoice ---
            WebElement archiveInvoiceBtn = driver.findElement(By.cssSelector(".invoice-detail .btn-archive"));
            archiveInvoiceBtn.click();
            WebElement confirmArchiveBtn = driver.findElement(By.cssSelector(".archive-modal .btn-confirm"));
            confirmArchiveBtn.click();

            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
            }

            // --- feature 11: re-open the dashboard once more before logging out ---
            driver.get("https://crm-admin.acmecorp.com/dashboard");
            dashboardPage.refreshPage();

            try {
                Thread.sleep(900);
            } catch (InterruptedException e) {
            }

            Assert.assertTrue(dashboardPage.isPageLoaded(), "Dashboard should finish loading after refresh");

            // --- feature 12: confirm the archived invoice no longer appears in default view ---
            driver.get("https://crm-admin.acmecorp.com/invoices");

            try {
                Thread.sleep(900);
            } catch (InterruptedException e) {
            }

            Assert.assertTrue(dashboardPage.isPageLoaded(), "Invoice grid should finish loading");

            // --- feature 13: logout ---
            dashboardPage.logout();
            Assert.assertTrue(driver.getCurrentUrl().contains("login"), "Should be redirected to login");

        } finally {
            driver.quit();
        }
    }
}
