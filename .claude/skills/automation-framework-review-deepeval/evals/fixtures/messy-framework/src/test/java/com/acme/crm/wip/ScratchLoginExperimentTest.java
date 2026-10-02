package com.acme.crm.wip;

import com.acme.crm.pages.LoginPage;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.annotations.Test;

/**
 * TODO: delete this or move it somewhere real - Dave, 2024
 */
public class ScratchLoginExperimentTest {

    @Test
    public void tryLoginWithWeirdCharsInPassword() {
        WebDriver driver = new ChromeDriver();
        LoginPage loginPage = new LoginPage(driver);
        driver.get("https://crm-admin.acmecorp.com/login");
        // just poking at this, not a real test yet
        loginPage.login("admin@acmecorp.com", "Admin123!@#$%");
        System.out.println("did it work? who knows");
        driver.quit();
    }
}
