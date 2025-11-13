from collective.deletepermission.tests.base import FunctionalTestCase
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME


class TestCopy(FunctionalTestCase):

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Contributor'])
        login(self.portal, TEST_USER_NAME)

    def test_copy_works_without_being_able_to_delete(self):
        folder = self.create_folder()
        self.revoke_permission('Delete portal content', on=folder)
        browser = self.get_browser()
        browser.login().open(folder)
        self.assertFalse(api.user.has_permission("Delete portal content", obj=folder))
        self.assertTrue(api.user.has_permission("Copy or Move", obj=folder))
        browser.find("Copy").click()
        # Check for success message (may vary by Plone version)
        info_msgs = browser.info_messages()
        self.assertTrue(
            any('copied' in msg.lower() for msg in info_msgs),
            f"Expected copy success message, got: {info_msgs}"
        )

    def test_copy_denied_without_copy_or_move_permission(self):
        folder = self.create_folder()
        self.revoke_permission('Copy or Move', on=folder)
        browser = self.get_browser()
        browser.login().open(folder)
        self.assertFalse(api.user.has_permission("Copy or Move", obj=folder))

        # Advanced users may guess the url.
        with browser.expect_unauthorized():
            browser.open(folder, view="object_copy")
