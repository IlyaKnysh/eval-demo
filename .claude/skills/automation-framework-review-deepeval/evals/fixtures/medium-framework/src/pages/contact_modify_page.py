class ContactModifyPage:
    """Page object for the Contact modification screen."""

    def __init__(self, page):
        self.page = page

    def wait_until_loaded(self):
        self.page.get_by_role("heading", name="Modify Contact").wait_for()

    def update_name(self, name: str):
        self.page.get_by_label("Contact name").fill(name)

    def update_status(self, status: str):
        self.page.get_by_role("combobox", name="Status").select_option(status)

    def save_changes(self):
        self.page.get_by_role("button", name="Save changes").click()
        self.page.get_by_text("Contact updated successfully").wait_for()

    def cancel_changes(self):
        self.page.get_by_role("button", name="Cancel").click()
