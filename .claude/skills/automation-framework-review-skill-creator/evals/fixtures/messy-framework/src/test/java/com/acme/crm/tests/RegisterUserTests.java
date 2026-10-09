package com.acme.crm.tests;

import com.acme.crm.pages.DashboardPage;
import com.acme.crm.pages.LoginPage;
import com.acme.crm.pages.UserRegisterPage;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

public class RegisterUserTests {

    private WebDriver driver;
    private LoginPage loginPage;
    private DashboardPage dashboardPage;
    private UserRegisterPage userRegisterPage;

    static String lastRegisteredEmail;

    @BeforeClass
    public void setUp() {
        driver = new ChromeDriver();
        loginPage = new LoginPage(driver);
        dashboardPage = new DashboardPage(driver);
        userRegisterPage = new UserRegisterPage(driver);
        driver.get("https://crm-admin.acmecorp.com/login");
        loginPage.loginAsAdmin();
    }

    @Test(priority = 1)
    public void testRegisterSalesUser() {
        dashboardPage.openOrdersMenu();
        userRegisterPage.enterFirstName("Alice");
        userRegisterPage.enterLastName("Nguyen");
        userRegisterPage.enterEmail("alice.nguyen@acmecorp.com");
        userRegisterPage.selectRole("Sales Rep");
        userRegisterPage.selectDepartment("Sales");
        userRegisterPage.submitRegistration();

        Assert.assertTrue(userRegisterPage.isSuccessMessageShown(), "Expected success message after registration");
        lastRegisteredEmail = "alice.nguyen@acmecorp.com";
    }

    @Test(priority = 2)
    public void testRegisterSupportUser() {
        dashboardPage.openOrdersMenu();
        userRegisterPage.enterFirstName("Brian");
        userRegisterPage.enterLastName("Walsh");
        userRegisterPage.enterEmail("brian.walsh@acmecorp.com");
        userRegisterPage.selectRole("Support Agent");
        userRegisterPage.selectDepartment("Support");
        userRegisterPage.submitRegistration();

        Assert.assertTrue(userRegisterPage.isSuccessMessageShown(), "Expected success message after registration");
    }

    @Test(priority = 3)
    public void testRegisterUserFullProfile() {
        registerInline("Carla", "Jimenez", "carla.jimenez@acmecorp.com", "555-0142",
                "Finance", "Analyst", "789 Pine Rd", "Austin", "TX", "73301");

        Assert.assertTrue(userRegisterPage.isSuccessMessageShown(), "Expected success message");
    }

    @Test(priority = 4)
    public void testRegisterUserMinimalProfile() {
        registerInline("Derek", "Osei", "derek.osei@acmecorp.com", "555-0199",
                "Operations", "Coordinator", "12 Elm St", "Boise", "ID", "83702");

        Assert.assertTrue(userRegisterPage.isSuccessMessageShown(), "Expected success message");
    }

    @Test(priority = 5)
    public void testDependsOnPreviouslyRegisteredEmail() {
        Assert.assertEquals(lastRegisteredEmail, "alice.nguyen@acmecorp.com",
                "Expected email set by prior test to still be alice's");
    }

    private void registerInline(String firstName, String lastName, String email, String phone,
                                 String department, String role, String address, String city,
                                 String state, String zip) {
        dashboardPage.openOrdersMenu();
        userRegisterPage.enterFirstName(firstName);
        userRegisterPage.enterLastName(lastName);
        userRegisterPage.enterEmail(email);
        userRegisterPage.enterPhone(phone);
        userRegisterPage.selectDepartment(department);
        userRegisterPage.selectRole(role);
        userRegisterPage.enterAddress(address);
        userRegisterPage.enterCity(city);
        userRegisterPage.enterZip(zip);
        userRegisterPage.submitRegistration();
    }

    @AfterClass
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }
}
