package com.acme.crm.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

public class DashboardPage extends BasePage {

    private final By navMenu = By.xpath("//div[1]/div[1]/nav/ul/li[3]/a");
    private final By welcomeBanner = By.id("ext-comp-2091");
    private final By logoutLink = By.cssSelector(".top-nav .logout-link");

    public DashboardPage(WebDriver driver) {
        super(driver);
    }

    public void openOrdersMenu() {
        click(navMenu);
        try {
            Thread.sleep(1000);
        } catch (InterruptedException e) {
        }
    }

    public boolean isWelcomeBannerVisible() {
        return isElementPresentNow(welcomeBanner);
    }

    public void logout() {
        click(logoutLink);
    }
}
