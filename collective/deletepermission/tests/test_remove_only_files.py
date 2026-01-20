from collective.deletepermission.tests.base import FunctionalTestCase


class TestOnlyFiles(FunctionalTestCase):

    def setUp(self):
        self.user_a = self.create_user(userid="usera")

        self.folder = self.create_folder(title="rootfolder")
        self.set_local_roles(self.folder, self.user_a, "Contributor")

        self.subfolder = self.create_folder(container=self.folder, title="subfolder")

        self.login(self.user_a)
        self.firstleveldoc = self.create_folder(
            container=self.folder, title="doc-firstleveldoc"
        )
        self.secondleveldoc = self.create_folder(
            container=self.subfolder, title="doc-secondleveldoc"
        )

    def test_delete_secondlevel(self):
        """Test if we are able to delete the file in the subfolder"""
        browser = self.get_browser()
        browser.login(self.user_a).open(
            self.secondleveldoc.absolute_url() + "/delete_confirmation"
        )
        browser.delete(self.secondleveldoc)

    def test_delete_firstlevel(self):
        """Test if we are able to delete the file in the rootfolder"""
        browser = self.get_browser()
        browser.login(self.user_a).open(
            self.firstleveldoc.absolute_url() + "/delete_confirmation"
        )
        browser.delete(self.firstleveldoc)

    def test_delete_subfolder(self):
        """Test if we can delete the subfolder. This should not be the case."""
        browser = self.get_browser()
        browser.login(self.user_a).open(
            self.subfolder.absolute_url() + "/delete_confirmation"
        )
        with browser.expect_unauthorized():
            browser.delete(self.subfolder)
