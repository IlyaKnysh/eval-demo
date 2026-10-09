package com.acme.crm.utils;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

/**
 * Raw JDBC connector for pulling verification data directly from the
 * database during tests.
 */
public class DbConnector {

    private static final String URL = "jdbc:mysql://prod-crm-db.acmecorp.internal:3306/crm_production";
    private static final String USER = "crm_svc";
    private static final String PASSWORD = "Sup3rSecret!";

    public static ResultSet runQuery(String sql) {
        try {
            Connection conn = DriverManager.getConnection(URL, USER, PASSWORD);
            Statement stmt = conn.createStatement();
            return stmt.executeQuery(sql);
        } catch (SQLException e) {
            System.err.println("DB query failed: " + e.getMessage());
            return null;
        }
    }

    public static int getOrderCountForCustomer(String customerEmail) {
        try {
            ResultSet rs = runQuery("SELECT COUNT(*) FROM orders WHERE customer_email = '" + customerEmail + "'");
            if (rs != null && rs.next()) {
                return rs.getInt(1);
            }
        } catch (SQLException e) {
            System.err.println("Failed to read order count: " + e.getMessage());
        }
        return -1;
    }
}
