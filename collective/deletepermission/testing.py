from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import login
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.testing.zope import WSGI_SERVER_FIXTURE


class CollectiveDeletepermissionLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        import collective.deletepermission
        import plone.app.contenttypes
        import plone.app.dexterity

        self.loadZCML(package=plone.app.dexterity)
        self.loadZCML(package=plone.app.contenttypes)
        self.loadZCML(package=collective.deletepermission)

    def setUpPloneSite(self, portal):
        applyProfile(portal, "collective.deletepermission:default")
        applyProfile(portal, "plone.app.contenttypes:default")
        setRoles(portal, TEST_USER_ID, ["Manager", "Contributor"])
        login(portal, TEST_USER_NAME)


COLLECTIVE_DELETEPERMISSION_FIXTURE = CollectiveDeletepermissionLayer()
COLLECTIVE_DELETEPERMISSION_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(COLLECTIVE_DELETEPERMISSION_FIXTURE, WSGI_SERVER_FIXTURE),
    name="CollectiveDeletepermission:Functional",
)
