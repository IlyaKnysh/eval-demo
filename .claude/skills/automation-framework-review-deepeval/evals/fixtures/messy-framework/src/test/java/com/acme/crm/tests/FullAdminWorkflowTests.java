package com.acme.crm.tests;

import com.acme.crm.pages.DashboardPage;
import com.acme.crm.pages.LoginPage;
import com.acme.crm.pages.OrderCreatePage;
import com.acme.crm.pages.OrderModifyPage;
import com.acme.crm.pages.UserManagement;
import com.acme.crm.pages.UserModifyPage;
import com.acme.crm.pages.UserRegisterPage;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Covers login, user registration, user modification, order creation,
 * order modification, and logout in sequence.
 */
public class FullAdminWorkflowTests {

    @Test
    public void testFullAdminWorkflowEndToEnd() {
        WebDriver driver = new ChromeDriver();
        try {
            LoginPage loginPage = new LoginPage(driver);
            DashboardPage dashboardPage = new DashboardPage(driver);
            UserRegisterPage userRegisterPage = new UserRegisterPage(driver);
            UserManagement userManagement = new UserManagement(driver);
            UserModifyPage userModifyPage = new UserModifyPage(driver);
            OrderCreatePage orderCreatePage = new OrderCreatePage(driver);
            OrderModifyPage orderModifyPage = new OrderModifyPage(driver);

            // --- feature 1: login ---
            driver.get("https://crm-admin.acmecorp.com/login");
            loginPage.login("admin@acmecorp.com", "Admin123!");
            Assert.assertFalse(loginPage.isErrorBannerShown(), "Login should succeed for admin");

            try {
                Thread.sleep(2000);
            } catch (InterruptedException e) {
            }

            Assert.assertTrue(dashboardPage.isWelcomeBannerVisible(), "Dashboard should show welcome banner");

            // --- feature 2: register a new user ---
            dashboardPage.openOrdersMenu();
            userRegisterPage.enterFirstName("Grace");
            userRegisterPage.enterLastName("Kim");
            userRegisterPage.enterEmail("grace.kim@acmecorp.com");
            userRegisterPage.enterPhone("555-0110");
            userRegisterPage.selectRole("Sales Rep");
            userRegisterPage.selectDepartment("Sales");
            userRegisterPage.enterAddress("55 Birch Ln");
            userRegisterPage.enterCity("Reno");
            userRegisterPage.enterZip("89501");
            userRegisterPage.submitRegistration();
            Assert.assertTrue(userRegisterPage.isSuccessMessageShown(), "User registration should succeed");

            try {
                Thread.sleep(1500);
            } catch (InterruptedException e) {
            }

            // --- feature 3: find and modify the user just created ---
            driver.get("https://crm-admin.acmecorp.com/users");
            userManagement.searchUser("grace.kim@acmecorp.com");

            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
                userManagement.log("interrupted during user search wait: " + e.getMessage());
            }

            userManagement.getFirstResultRow().click();
            userModifyPage.verifyFieldIsEditableAndEnabled();
            userModifyPage.enterName("Grace Kim-Anderson");
            userModifyPage.selectStatus("Active");
            userModifyPage.enterEmail("grace.kimanderson@acmecorp.com");
            userModifyPage.clickSave();

            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
            }

            // --- feature 4: create an order for the modified user ---
            dashboardPage.openOrdersMenu();
            orderCreatePage.enterCustomerName("Grace Kim-Anderson");
            orderCreatePage.enterCustomerEmail("grace.kimanderson@acmecorp.com");
            orderCreatePage.selectProduct("Widget Deluxe");
            orderCreatePage.enterQuantity("4");
            orderCreatePage.enterShippingAddress("55 Birch Ln, Reno, NV 89501");
            orderCreatePage.enterBillingAddress("55 Birch Ln, Reno, NV 89501");
            orderCreatePage.selectPaymentMethod("Credit Card");
            orderCreatePage.enterNotes("VIP customer, expedite shipping");
            orderCreatePage.submit();

            String orderId = orderCreatePage.getConfirmationOrderId();
            Assert.assertNotNull(orderId, "Order should be created for the new user");

            try {
                Thread.sleep(2000);
            } catch (InterruptedException e) {
            }

            // --- feature 5: modify the order status ---
            driver.get("https://crm-admin.acmecorp.com/orders");
            orderModifyPage.verifyFieldIsEditableAndEnabled();
            orderModifyPage.enterName("Grace Kim-Anderson - priority order");
            orderModifyPage.selectStatus("Processing");
            orderModifyPage.clickSave();

            try {
                Thread.sleep(1500);
            } catch (InterruptedException e) {
            }

            // --- feature 6: verify dashboard reflects the new order count ---
            driver.get("https://crm-admin.acmecorp.com/dashboard");
            Assert.assertTrue(dashboardPage.isWelcomeBannerVisible(), "Dashboard should reload after workflow");

            // --- feature 7: log back in to verify audit trail persisted ---
            loginPage.login("admin@acmecorp.com", "Admin123!");

            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
            }

            Assert.assertTrue(dashboardPage.isWelcomeBannerVisible(), "Should be able to log back in after logout");

            // --- feature 8: re-open the order and confirm the status stuck ---
            driver.get("https://crm-admin.acmecorp.com/orders");
            orderModifyPage.verifyFieldIsEditableAndEnabled();

            try {
                Thread.sleep(800);
            } catch (InterruptedException e) {
            }

            // --- feature 9: navigate to dashboard once more before final logout ---
            driver.get("https://crm-admin.acmecorp.com/dashboard");
            dashboardPage.refreshPage();
            Assert.assertTrue(dashboardPage.isPageLoaded(), "Dashboard should finish loading after refresh");

            // --- feature 10: check the user grid still lists the modified user ---
            driver.get("https://crm-admin.acmecorp.com/users");
            userManagement.searchUser("grace.kimanderson@acmecorp.com");

            try {
                Thread.sleep(900);
            } catch (InterruptedException e) {
            }

            Assert.assertTrue(userManagement.isPageLoaded(), "User grid should finish loading after search");

            // --- feature 11: final logout ---
            dashboardPage.logout();
            Assert.assertTrue(driver.getCurrentUrl().contains("login"), "Should be redirected to login after logout");

        } finally {
            driver.quit();
        }
    }
}
