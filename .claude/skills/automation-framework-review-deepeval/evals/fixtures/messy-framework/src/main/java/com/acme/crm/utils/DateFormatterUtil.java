package com.acme.crm.utils;

import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * Date formatting helpers used across pages and tests.
 */
public class DateFormatterUtil {

    public static String formatToday(String pattern) {
        return new SimpleDateFormat(pattern).format(new Date());
    }

    public static String formatTimestampForFilename() {
        return new SimpleDateFormat("yyyyMMdd_HHmmss").format(new Date());
    }
}
