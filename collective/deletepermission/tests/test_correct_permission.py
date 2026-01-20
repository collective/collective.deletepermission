from AccessControl import Unauthorized
from collective.deletepermission.tests.base import FunctionalTestCase
from zExceptions import BadRequest


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

    def test_usera_remove_folder(self):
        """Test if usera can remove his folder"""
        self.login(self.user_a)
        self.folder.manage_delObjects("folder-a")

    def test_userb_remove_folder(self):
        """Test if userb can't delete usera's folder"""
        self.login(self.user_b)
        self.assertRaises(Unauthorized, self.folder.manage_delObjects, "folder-a")

    def test_usera_remove_doc_a(self):
        """Test if usera can remove his doc"""
        self.login(self.user_a)
        self.folder_a.manage_delObjects("doc-a")

    def test_usera_remove_doc_b(self):
        """Test if usera can remove userb's folder"""
        self.login(self.user_a)
        self.folder_a.manage_delObjects("doc-b")

    def test_userb_remove_doc_a(self):
        """Test if userb can remove usera's folder"""
        self.login(self.user_b)
        self.assertRaises(Unauthorized, self.folder_a.manage_delObjects, "doc-a")

    def test_userb_remove_doc_b(self):
        """Test if userb can remove his doc"""
        self.login(self.user_b)
        self.folder_a.manage_delObjects("doc-b")

    def test_remove_multiple(self):
        """Test if we still are able to remove multiple objects at once."""
        self.login(self.user_a)
        self.folder_a.manage_delObjects(["doc-a", "doc-b"])
        self.assertEqual(self.folder_a.objectIds(), [])

    def test_remove_empty(self):
        """Check that passing None raises BadRequest in Plone 6/Zope 5."""
        self.login(self.user_a)
        self.assertRaises(BadRequest, self.folder_a.manage_delObjects, None)
