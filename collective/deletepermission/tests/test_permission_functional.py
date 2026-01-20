from collective.deletepermission.tests.base import FunctionalTestCase


class TestCorrectPermissions(FunctionalTestCase):

    def setUp(self):
        self.user_a = self.create_user(userid="usera")
        self.user_b = self.create_user(userid="userb")

        self.folder = self.create_folder(title="rootfolder")
        self.set_local_roles(self.folder, self.user_a, "Contributor")
        self.set_local_roles(self.folder, self.user_b, "Contributor")

        self.login(self.user_a)
        self.folder_a = self.create_folder(container=self.folder, title="folder-a")
        self.doc_a = self.create_folder(container=self.folder_a, title="doc-a")

        self.login(self.user_b)
        self.doc_b = self.create_folder(container=self.folder_a, title="doc-b")

    def test_userb_delete_docb(self):
        """
        Check if User B is able to delete his own document.
        """
        browser = self.get_browser()
        browser.login(self.user_b).open(
            self.doc_b.absolute_url() + "/delete_confirmation"
        )
        browser.delete(self.doc_b)

    def test_userb_cut_docb(self):
        """
        Check if User B is able to cut his own document.
        """
        browser = self.get_browser()
        browser.login(self.user_b).open(self.doc_b.absolute_url())
        browser.cut(self.doc_b)

    def test_userb_rename_docb(self):
        """
        Check if User B is able to rename his own document.
        """
        browser = self.get_browser()
        browser.login(self.user_b).open(self.doc_b.absolute_url())
        browser.rename(self.doc_b, "doc-b-renamed")
        browser.assert_no_error_messages()
        self.assertEqual(self.folder_a.absolute_url() + "/doc-b-renamed", browser.url)

    def test_usera_remove_folder(self):
        """
        Test if User A is able to delete his folder
        """
        browser = self.get_browser()
        browser.login(self.user_a).open(
            self.folder_a.absolute_url() + "/delete_confirmation"
        )
        browser.delete(self.folder_a)

    def test_usera_cut_folder(self):
        """
        Test if User A is able to cut his folder
        """
        browser = self.get_browser()
        browser.login(self.user_a).open(self.folder_a.absolute_url())
        browser.cut(self.folder_a)

    def test_usera_rename_folder(self):
        """
        Test if User A is able to rename his folder
        """
        browser = self.get_browser()
        browser.login(self.user_a).open(self.folder_a.absolute_url())
        browser.rename(self.folder_a, "folder-a-renamed")
        browser.assert_no_error_messages()
        self.assertEqual(self.folder.absolute_url() + "/folder-a-renamed", browser.url)

    def test_userb_remove_folder(self):
        """
        Check if User B can delete User A's folder. Should not be possible.
        """
        browser = self.get_browser()
        browser.login(self.user_b).open(
            self.folder_a.absolute_url() + "/delete_confirmation"
        )
        with browser.expect_unauthorized():
            browser.delete(self.folder_a)

    def test_userb_cut_folder(self):
        """
        Check if User B can't cut User A's folder.
        """
        browser = self.get_browser()
        browser.login(self.user_b).open(self.folder_a.absolute_url())
        self.assertNotIn("Cut", self.get_actions(self.folder_a))
        with browser.expect_unauthorized():
            browser.open(self.folder_a.absolute_url() + "/object_cut")

    def test_userb_rename_folder(self):
        """
        Check if User B can't rename User A's folder.
        """
        browser = self.get_browser()
        browser.login(self.user_b).open(self.folder_a.absolute_url())
        self.assertNotIn("Rename", self.get_actions(self.folder_a))
        with browser.expect_unauthorized():
            browser.open(self.folder_a.absolute_url() + "/object_rename")

    def test_usera_remove_doc_a(self):
        """
        Test if User A is able to delete his own Document.
        """
        browser = self.get_browser()
        browser.login(self.user_a).open(
            self.doc_a.absolute_url() + "/delete_confirmation"
        )
        browser.delete(self.doc_a)

    def test_usera_cut_doc_a(self):
        """
        Test if User A is able to cut his own Document.
        """
        browser = self.get_browser()
        browser.login(self.user_a).open(self.doc_a.absolute_url())
        browser.cut(self.doc_a)

    def test_usera_rename_doc_a(self):
        """
        Test if User A is able to rename his own Document.
        """
        browser = self.get_browser()
        browser.login(self.user_a).open(self.doc_a.absolute_url())
        browser.rename(self.doc_a, "doc-a-renamed")
        browser.assert_no_error_messages()
        self.assertEqual(self.folder_a.absolute_url() + "/doc-a-renamed", browser.url)

    def test_usera_remove_doc_b(self):
        """
        Test if User A is able to delete the Document of User B
        """
        browser = self.get_browser()
        browser.login(self.user_a).open(
            self.doc_b.absolute_url() + "/delete_confirmation"
        )
        browser.delete(self.doc_b)

    def test_usera_cut_doc_b(self):
        """
        Test if User A is able to cut the Document of User B
        """
        browser = self.get_browser()
        browser.login(self.user_a).open(self.doc_b.absolute_url())
        browser.cut(self.doc_b)

    def test_usera_rename_doc_b(self):
        """
        Test if User A is able to rename the Document of User B
        """
        browser = self.get_browser()
        browser.login(self.user_a).open(self.doc_b.absolute_url())
        browser.rename(self.doc_b, "doc-b-renamed")
        browser.assert_no_error_messages()
        self.assertEqual(self.folder_a.absolute_url() + "/doc-b-renamed", browser.url)

    def test_userb_remove_doc_a(self):
        """
        Check if User B can remove User A's Document. Should not be possible.
        """
        browser = self.get_browser()
        browser.login(self.user_b).open(
            self.doc_a.absolute_url() + "/delete_confirmation"
        )
        with browser.expect_unauthorized():
            browser.delete(self.doc_a)

    def test_userb_cut_doc_a(self):
        """
        Check if User B can't remove User A's Document.
        """
        browser = self.get_browser()
        browser.login(self.user_b).open(self.doc_a.absolute_url())
        self.assertNotIn("Cut", self.get_actions(self.doc_a))
        with browser.expect_unauthorized():
            browser.open(self.doc_a.absolute_url() + "/object_cut")

    def test_userb_rename_doc_a(self):
        """
        Check if User B can't rename User A's Document.
        """
        browser = self.get_browser()
        browser.login(self.user_b).open(self.doc_a.absolute_url())
        self.assertNotIn("Rename", self.get_actions(self.doc_a))
        with browser.expect_unauthorized():
            browser.open(self.doc_a.absolute_url() + "/object_rename")
