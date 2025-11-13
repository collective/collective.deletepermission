from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.SecurityManagement import setSecurityManager
from collective.deletepermission import testing
from contextlib import contextmanager
from ftw.testbrowser.pages import editbar
from plone import api
from plone.app.testing import login
from unittest import TestCase
import transaction


class FunctionalTestCase(TestCase):

    layer = testing.COLLECTIVE_DELETEPERMISSION_FUNCTIONAL_TESTING

    def revoke_permission(self, permission, on):
        on.manage_permission(permission, roles=[], acquire=False)
        transaction.commit()

    def set_local_roles(self, context, user, *roles):
        if hasattr(user, 'id'):
            user = user.id
        elif hasattr(user, 'getUserName'):
            user = user.getUserName()

        context.manage_setLocalRoles(user, tuple(roles))
        context.reindexObjectSecurity()
        transaction.commit()

    def get_actions(self):
        return editbar.menu_options("Actions")

    @contextmanager
    def user(self, username):
        if hasattr(username, 'id'):
            username = username.id
        elif hasattr(username, 'getUserName'):
            username = username.getUserName()

        sm = getSecurityManager()
        login(self.layer['portal'], username)
        try:
            yield
        finally:
            setSecurityManager(sm)

    def create_user(self, userid=None, email=None, username=None, fullname=None, roles=None):
        """Helper to create a user."""
        if userid is None:
            userid = 'testuser'
        if email is None:
            email = f'{userid}@example.com'

        user = api.user.create(
            email=email,
            username=userid,
            properties={
                'fullname': fullname or userid,
            }
        )

        if roles:
            api.user.grant_roles(username=userid, roles=list(roles))

        transaction.commit()
        return user

    def create_folder(self, container=None, title=None, id=None):
        """Helper to create a folder."""
        if container is None:
            container = self.layer['portal']

        folder = api.content.create(
            container=container,
            type='Folder',
            title=title or 'Test Folder',
            id=id,
            safe_id=True if id is None else False,
        )
        transaction.commit()
        return folder
