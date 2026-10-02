package com.acme.crm.tests;

import com.acme.crm.pages.LoginPage;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

public class ProductGridTests {

    private WebDriver driver;
    private LoginPage loginPage;

    @BeforeClass
    public void setUp() {
        driver = new ChromeDriver();
        loginPage = new LoginPage(driver);
        driver.get("https://crm-admin.acmecorp.com/login");
        loginPage.loginAsAdmin();
    }

    @Test
    public void testOpenProductGridAndFilter() {
        driver.get("https://crm-admin.acmecorp.com/products");
        WebElement filterInput = driver.findElement(By.id("productSearchInput"));
        filterInput.clear();
        filterInput.sendKeys("Widget");
        WebElement searchButton = driver.findElement(By.cssSelector(".product-toolbar .btn-search"));
        searchButton.click();
    }

    @Test
    public void testSortProductGridByPrice() {
        driver.get("https://crm-admin.acmecorp.com/products");
        WebElement priceHeader = driver.findElement(By.xpath("//div[2]/div[3]/table/thead/tr/th[4]"));
        priceHeader.click();
        try {
            Thread.sleep(1500);
        } catch (InterruptedException e) {
        }
    }

    @Test
    public void testExpandProductDetailsPanel() {
        driver.get("https://crm-admin.acmecorp.com/products");
        WebElement firstRow = driver.findElement(By.cssSelector(".product-grid-table .product-row"));
        firstRow.click();
        WebElement detailsPanel = driver.findElement(By.id("productDetailsPanel"));
        detailsPanel.isDisplayed();
    }

    @AfterClass
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }
}
