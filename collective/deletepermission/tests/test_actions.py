from collective.deletepermission.tests.base import FunctionalTestCase

import transaction


class TestDeleteAction(FunctionalTestCase):

    def setUp(self):
        self.hugo = self.create_user(
            userid="hugo", fullname="Hugo Boss", roles=["Member", "Contributor"]
        )
        self.john = self.create_user(
            userid="john", fullname="John Doe", roles=["Member", "Contributor"]
        )
        self.login(self.hugo)
        self.container = self.create_folder()
        self.login(self.john)
        self.content = self.create_folder(container=self.container)

    def test_user_can_delete_own_contents(self):
        browser = self.get_browser()
        browser.login(self.john).open(self.content.absolute_url())
        self.assertIn(
            "Delete",
            self.get_actions(self.content),
            "A user should be able to delete his own content.",
        )

    def test_user_can_not_delete_without_delete_objects_on_parent(self):
        self.revoke_permission("Delete objects", on=self.container)
        transaction.commit()
        browser = self.get_browser()
        browser.login(self.john).open(self.content.absolute_url())
        self.assertNotIn(
            "Delete",
            self.get_actions(self.content),
            "A user should not be able to delete content"
            ' without "Delete objects" on the parent.',
        )


class TestCutAction(FunctionalTestCase):

    def setUp(self):
        self.hugo = self.create_user(
            userid="hugo", fullname="Hugo Boss", roles=["Member", "Contributor"]
        )
        self.john = self.create_user(
            userid="john", fullname="John Doe", roles=["Member", "Contributor"]
        )
        self.login(self.hugo)
        self.container = self.create_folder()
        self.login(self.john)
        self.content = self.create_folder(container=self.container)

    def test_user_can_cut_own_contents(self):
        browser = self.get_browser()
        browser.login(self.john).open(self.content.absolute_url())
        self.assertIn(
            "Cut",
            self.get_actions(self.content),
            "A user should be able to cut his own content.",
        )

    def test_user_can_not_cut_without_delete_objects_on_parent(self):
        self.revoke_permission("Delete objects", on=self.container)
        transaction.commit()
        browser = self.get_browser()
        browser.login(self.john).open(self.content.absolute_url())
        self.assertNotIn(
            "Cut",
            self.get_actions(self.content),
            "A user should not be able to cut content"
            ' without "Delete objects" on the parent.',
        )
