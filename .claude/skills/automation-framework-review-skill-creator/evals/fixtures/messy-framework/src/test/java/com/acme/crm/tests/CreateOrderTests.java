package com.acme.crm.tests;

import com.acme.crm.pages.DashboardPage;
import com.acme.crm.pages.LoginPage;
import com.acme.crm.pages.OrderCreatePage;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

public class CreateOrderTests {

    private WebDriver driver;
    private LoginPage loginPage;
    private DashboardPage dashboardPage;
    private OrderCreatePage orderCreatePage;

    static String orderIdFromFirstTest;

    @BeforeClass
    public void setUp() {
        driver = new ChromeDriver();
        loginPage = new LoginPage(driver);
        dashboardPage = new DashboardPage(driver);
        orderCreatePage = new OrderCreatePage(driver);
        driver.get("https://crm-admin.acmecorp.com/login");
        loginPage.loginAsAdmin();
    }

    @Test(priority = 1)
    public void testCreateStandardOrder() {
        dashboardPage.openOrdersMenu();
        orderCreatePage.enterCustomerName("John Doe");
        orderCreatePage.enterCustomerEmail("john.doe@example.com");
        orderCreatePage.selectProduct("Widget Pro");
        orderCreatePage.enterQuantity("5");
        orderCreatePage.submit();

        String orderId = orderCreatePage.getConfirmationOrderId();
        Assert.assertNotNull(orderId, "Order ID should not be null after creation");
        orderIdFromFirstTest = orderId;
    }

    @Test(priority = 2)
    public void testCreateOrderWithDiscountCode() {
        dashboardPage.openOrdersMenu();
        orderCreatePage.enterCustomerName("Jane Smith");
        orderCreatePage.enterCustomerEmail("jane.smith@example.com");
        orderCreatePage.selectProduct("Widget Standard");
        orderCreatePage.enterQuantity("2");
        orderCreatePage.enterDiscountCode("SAVE10");
        orderCreatePage.submit();

        String orderId = orderCreatePage.getConfirmationOrderId();
        Assert.assertNotNull(orderId, "Order ID should not be null after creation with discount");
    }

    @Test(priority = 3)
    public void testCreateOrderFullDetails() {
        createOrderInline("Robert Chen", "robert.chen@example.com", "Widget Deluxe", "10",
                "123 Main St", "Springfield", "IL", "62704", "Credit Card", "SAVE10",
                "Please deliver before Friday");

        String orderId = orderCreatePage.getConfirmationOrderId();
        Assert.assertNotNull(orderId, "Order ID should not be null");
    }

    @Test(priority = 4)
    public void testCreateOrderNoDiscount() {
        createOrderInline("Maria Garcia", "maria.garcia@example.com", "Widget Pro", "1",
                "456 Oak Ave", "Denver", "CO", "80202", "PayPal", "",
                "Gift wrap requested");

        String orderId = orderCreatePage.getConfirmationOrderId();
        Assert.assertNotNull(orderId, "Order ID should not be null");
    }

    @Test(priority = 5)
    public void testReuseOrderIdFromEarlierTest() {
        Assert.assertNotNull(orderIdFromFirstTest, "Expected order id to have been set by a prior test");
        dashboardPage.openOrdersMenu();
        orderCreatePage.enterNotes("Follow-up note for order " + orderIdFromFirstTest);
    }

    // helper that just packs args into calls - not a real builder/factory
    private void createOrderInline(String name, String email, String product, String qty,
                                    String shipping, String city, String state, String zip,
                                    String paymentMethod, String discountCode, String notes) {
        dashboardPage.openOrdersMenu();
        orderCreatePage.enterCustomerName(name);
        orderCreatePage.enterCustomerEmail(email);
        orderCreatePage.selectProduct(product);
        orderCreatePage.enterQuantity(qty);
        orderCreatePage.enterShippingAddress(shipping + ", " + city + ", " + state + " " + zip);
        orderCreatePage.enterBillingAddress(shipping + ", " + city + ", " + state + " " + zip);
        orderCreatePage.selectPaymentMethod(paymentMethod);
        orderCreatePage.enterDiscountCode(discountCode);
        orderCreatePage.enterNotes(notes);
        orderCreatePage.submit();
    }

    @AfterClass
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }
}
