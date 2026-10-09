class AdminConsole:
    """Page object for the top-level admin console shell (nav bar, user menu).

    Does not follow the repo's *Page naming convention used by every other
    page object in this package (compare LoginPage, DashboardPage,
    AccountModifyPage, etc.).
    """

    def __init__(self, page):
        self.page = page

    def open_user_menu(self):
        self.page.get_by_role("button", name="Account menu").click()

    def logout(self):
        self.open_user_menu()
        self.page.get_by_role("menuitem", name="Log out").click()

    def switch_workspace(self, workspace_name: str):
        self.page.get_by_role("button", name="Workspace switcher").click()
        self.page.get_by_role("option", name=workspace_name).click()
