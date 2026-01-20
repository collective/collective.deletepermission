from collective.deletepermission.tests.base import FunctionalTestCase
from plone import api

import transaction


class TestFactoryPatch(FunctionalTestCase):

    def test_object_addable_without_delete_permission(self):
        """Test that objects can be created without delete permission."""
        user = self.create_user(userid="testuser", roles=["Contributor"])
        self.revoke_permission("Delete portal content", on=self.layer["portal"])
        transaction.commit()

        # Use plone.api to create content directly
        self.login(user)
        folder = api.content.create(
            container=self.layer["portal"], type="Folder", title="Foo"
        )
        transaction.commit()
        # Verify the folder was created
        self.assertIsNotNone(folder)
        self.assertEqual(folder.Title(), "Foo")
