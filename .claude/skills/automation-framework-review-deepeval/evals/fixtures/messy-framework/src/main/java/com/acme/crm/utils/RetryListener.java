package com.acme.crm.utils;

import org.testng.IRetryAnalyzer;
import org.testng.ITestResult;

/**
 * Retry-on-failure analyzer, configured suite-wide via testng.xml's
 * retryCount parameter.
 */
public class RetryListener implements IRetryAnalyzer {

    private int retryCount = 0;
    private static final int MAX_RETRY_COUNT = 3;

    @Override
    public boolean retry(ITestResult result) {
        if (retryCount < MAX_RETRY_COUNT) {
            retryCount++;
            return true;
        }
        return false;
    }
}
