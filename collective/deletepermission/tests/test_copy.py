from collective.deletepermission.tests.base import FunctionalTestCase
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME


class TestCopy(FunctionalTestCase):

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        login(self.portal, TEST_USER_NAME)

    def test_copy_works_without_being_able_to_delete(self):
        folder = self.create_folder()
        self.revoke_permission("Delete portal content", on=folder)
        browser = self.get_browser()
        browser.login().open(folder.absolute_url())
        self.assertFalse(api.user.has_permission("Delete portal content", obj=folder))
        self.assertTrue(api.user.has_permission("Copy or Move", obj=folder))
        # Copy should succeed without raising Unauthorized
        browser.copy(folder)
        # Verify no error by checking response status (200 = OK)
        self.assertEqual(browser._last_response.status_code, 200)

    def test_copy_denied_without_copy_or_move_permission(self):
        folder = self.create_folder()
        self.revoke_permission("Copy or Move", on=folder)
        browser = self.get_browser()
        browser.login().open(folder.absolute_url())
        self.assertFalse(api.user.has_permission("Copy or Move", obj=folder))

        with browser.expect_unauthorized():
            browser.open(folder.absolute_url() + "/object_copy")
