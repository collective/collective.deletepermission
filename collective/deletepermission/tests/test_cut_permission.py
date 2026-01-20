from collective.deletepermission.tests.base import FunctionalTestCase
from OFS.CopySupport import CopyError


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

    def test_usera_cut_folder(self):
        """usera should be able to cut his own folder
        becauase he is its Owner"""
        self.login(self.user_a)
        self.folder.manage_cutObjects(["folder-a"])

    def test_userb_cut_folder(self):
        """userb should NOT be able to cut usera's folder, because he is
        not its Owner"""
        self.login(self.user_b)
        self.assertRaises(CopyError, self.folder.manage_cutObjects, ["folder-a"])

    def test_usera_cut_doc_a(self):
        """usera should be able to cut doc-a, because he is its Owner"""
        self.login(self.user_a)
        self.folder_a.manage_cutObjects(["doc-a"])

    def test_usera_cut_doc_b(self):
        """usera should be able to cut doc-b, because ???????????????????"""
        # XXX why?
        self.login(self.user_a)
        self.folder_a.manage_cutObjects(["doc-b"])

    def test_userb_cut_doc_a(self):
        """userb should NOT be able to cut coc-a, because his not Owner"""
        # XXX should this be raised upon paste??
        self.login(self.user_b)
        self.assertRaises(CopyError, self.folder_a.manage_cutObjects, "doc-a")

    def test_userb_cut_doc_b(self):
        """userb should be able to cut his own document"""
        self.login(self.user_b)
        self.folder_a.manage_cutObjects(["doc-b"])

    def test_cut_multiple(self):
        """Cutting objects INCLUDING an object which cannot be cut should not
        raise, so that the OTHER object is cut (not the transaction not
        cancelled because of the exception)
        """
        self.login(self.user_a)
        self.folder_a.manage_cutObjects(["doc-a", "doc-b"])

    def test_cut_empty(self):
        """Cutting "None" should throw a ValueError."""
        self.login(self.user_a)
        self.assertRaises(ValueError, self.folder_a.manage_cutObjects, None)
