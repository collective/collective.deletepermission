from collective.deletepermission.tests.base import FunctionalTestCase
from ftw.testbrowser import browsing


class TestOnlyFiles(FunctionalTestCase):

    def setUp(self):
        self.user_a = self.create_user(userid='usera')

        self.folder = self.create_folder(title='rootfolder')
        self.set_local_roles(self.folder, self.user_a, 'Contributor')

        self.subfolder = self.create_folder(
            container=self.folder,
            title='subfolder'
        )

        with self.user(self.user_a):
            self.firstleveldoc = self.create_folder(
                container=self.folder,
                title='doc-firstleveldoc'
            )
            self.secondleveldoc = self.create_folder(
                container=self.subfolder,
                title='doc-secondleveldoc'
            )

    @browsing
    def test_delete_secondlevel(self, browser):
        """Test if we are able to delete the file in the subfolder"""
        browser.login(self.user_a).open(self.secondleveldoc, view='delete_confirmation')
        browser.find('Delete').click()

    @browsing
    def test_delete_firstlevel(self, browser):
        """Test if we are able to delete the file in the rootfolder"""
        browser.login(self.user_a).open(self.firstleveldoc, view='delete_confirmation')
        browser.find('Delete').click()

    @browsing
    def test_delete_subfolder(self, browser):
        """Test if we can delete the subfolder. This should not be the case."""
        browser.login(self.user_a).open(self.subfolder, view='delete_confirmation')
        with browser.expect_unauthorized():
            browser.find('Delete').click()
