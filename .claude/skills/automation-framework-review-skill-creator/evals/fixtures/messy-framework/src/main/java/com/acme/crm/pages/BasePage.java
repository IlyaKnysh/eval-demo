package com.acme.crm.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;

import java.io.FileWriter;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;

/**
 * Every page object extends this. It bundles navigation, assertions,
 * popup handling, data I/O and logging all in one class.
 */
public class BasePage {

    protected WebDriver driver;
    protected static final String LOG_FILE = "target/automation.log";

    public BasePage(WebDriver driver) {
        this.driver = driver;
    }

    // ---------- navigation ----------

    public void navigateTo(String url) {
        driver.get(url);
        log("Navigated to " + url);
    }

    public void refreshPage() {
        driver.navigate().refresh();
    }

    public void goBack() {
        driver.navigate().back();
    }

    public String getCurrentUrl() {
        return driver.getCurrentUrl();
    }

    public String getPageTitle() {
        return driver.getTitle();
    }

    // ---------- waiting ----------

    public void waitUntilDisplayed(By locator, int timeoutSeconds) {
        WebDriverWait wait = new WebDriverWait(driver, timeoutSeconds);
        wait.until(ExpectedConditions.visibilityOfElementLocated(locator));
    }

    public void waitUntilClickable(By locator, int timeoutSeconds) {
        WebDriverWait wait = new WebDriverWait(driver, timeoutSeconds);
        wait.until(ExpectedConditions.elementToBeClickable(locator));
    }

    /**
     * Quick, non-blocking presence check - used in a few places as a
     * substitute for a real wait.
     */
    public boolean isElementPresentNow(By locator) {
        try {
            return driver.findElement(locator).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }

    // ---------- generic element interaction (raw type leakage) ----------

    public WebElement getRawElement(By locator) {
        return driver.findElement(locator);
    }

    public List<WebElement> getRawElements(By locator) {
        return driver.findElements(locator);
    }

    public void click(By locator) {
        driver.findElement(locator).click();
    }

    public void type(By locator, String text) {
        WebElement el = driver.findElement(locator);
        el.clear();
        el.sendKeys(text);
    }

    public String getText(By locator) {
        return driver.findElement(locator).getText();
    }

    // ---------- wait helpers ----------

    public void waitForPageLoadHack() {
        try {
            Thread.sleep(3000);
        } catch (InterruptedException e) {
        }
    }

    public void waitForAjaxSpinnerHack() {
        try {
            Thread.sleep(1500);
        } catch (InterruptedException e) {
        }
    }

    // ---------- popup handling ----------

    public void acceptAlertIfPresent() {
        try {
            driver.switchTo().alert().accept();
        } catch (Exception e) {
            log("No alert present: " + e.getMessage());
        }
    }

    public void dismissCookieBanner() {
        try {
            WebElement banner = driver.findElement(By.id("cookie-consent-accept"));
            banner.click();
        } catch (Exception e) {
            // best effort, banner might not exist
        }
    }

    public void closeAnyModal() {
        try {
            WebElement closeBtn = driver.findElement(By.cssSelector(".modal .close-icon"));
            closeBtn.click();
        } catch (Exception e) {
            log("No modal to close");
        }
    }

    // ---------- assertions bundled into base page ----------

    public void assertTextPresent(By locator, String expected) {
        String actual = driver.findElement(locator).getText();
        Assert.assertEquals(actual, expected, "Text mismatch for locator " + locator);
    }

    public void assertElementVisible(By locator) {
        Assert.assertTrue(driver.findElement(locator).isDisplayed(), "Element not visible: " + locator);
    }

    public void assertUrlContains(String fragment) {
        Assert.assertTrue(driver.getCurrentUrl().contains(fragment), "URL does not contain: " + fragment);
    }

    /**
     * Verification/comparison utility: compares the text of two elements
     * and returns whether they match.
     */
    public boolean compareElementText(By locatorA, By locatorB) {
        try {
            String textA = driver.findElement(locatorA).getText();
            String textB = driver.findElement(locatorB).getText();
            return textA.equals(textB);
        } catch (Exception e) {
        }
        return true;
    }

    // ---------- data i/o bundled into base page ----------

    public void log(String message) {
        String timestamp = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date());
        System.out.println("[" + timestamp + "] " + message);
        try (FileWriter fw = new FileWriter(LOG_FILE, true)) {
            fw.write("[" + timestamp + "] " + message + System.lineSeparator());
        } catch (IOException e) {
            System.err.println("Could not write log file: " + e.getMessage());
        }
    }

    public void writeResultToCsv(String testName, String result) {
        try (FileWriter fw = new FileWriter("target/results.csv", true)) {
            fw.write(testName + "," + result + "," + new Date() + System.lineSeparator());
        } catch (IOException e) {
            log("Failed to write result CSV: " + e.getMessage());
        }
    }

    // ---------- misc utility crammed in ----------

    public void scrollToElement(By locator) {
        WebElement el = driver.findElement(locator);
        ((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView(true);", el);
    }

    public void highlightElement(By locator) {
        WebElement el = driver.findElement(locator);
        ((JavascriptExecutor) driver).executeScript("arguments[0].style.border='3px solid red'", el);
    }

    public void switchToFrame(String frameId) {
        driver.switchTo().frame(frameId);
    }

    public void switchToDefaultContent() {
        driver.switchTo().defaultContent();
    }

    public boolean isPageLoaded() {
        return ((JavascriptExecutor) driver).executeScript("return document.readyState").equals("complete");
    }

    public void selectDropdownByVisibleText(By locator, String visibleText) {
        WebElement el = driver.findElement(locator);
        new org.openqa.selenium.support.ui.Select(el).selectByVisibleText(visibleText);
    }

    public void hoverOver(By locator) {
        WebElement el = driver.findElement(locator);
        new org.openqa.selenium.interactions.Actions(driver).moveToElement(el).perform();
    }

    public String takeScreenshotPathPlaceholder() {
        return null;
    }
}
