# CRM Admin UI Tests

Selenium + TestNG UI automation for the Acme CRM admin console (users, orders, products, invoices).

## Stack

- Java 8
- Selenium 3.141.59
- TestNG 6.14.3
- Maven Surefire

## Running the suite

```
mvn clean test
```

Configuration (URLs, credentials) lives in `src/test/resources/config.properties`.

## Structure

- `src/main/java/com/acme/crm/pages` - page objects
- `src/main/java/com/acme/crm/utils` - shared utilities
- `src/test/java/com/acme/crm/tests` - test classes
- `testng.xml` - suite definition
