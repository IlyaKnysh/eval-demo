"""Semantic get_by_role / get_by_test_id locators used consistently across
all page objects (no CSS/XPath scraping)."""


class LoginPage:
    def __init__(self, page):
        self.page = page

    def goto(self):
        self.page.goto("/login")

    def login(self, username: str, password: str):
        self.page.get_by_label("Username").fill(username)
        self.page.get_by_label("Password").fill(password)
        self.page.get_by_role("button", name="Sign in").click()
