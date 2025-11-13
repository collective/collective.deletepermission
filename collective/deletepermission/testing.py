from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import setRoles, TEST_USER_ID, TEST_USER_NAME, login


class CollectiveDeletepermissionLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        import plone.app.dexterity
        import plone.app.contenttypes
        import collective.deletepermission
        self.loadZCML(package=plone.app.dexterity)
        self.loadZCML(package=plone.app.contenttypes)
        self.loadZCML(package=collective.deletepermission)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'collective.deletepermission:default')
        applyProfile(portal, 'plone.app.contenttypes:default')
        setRoles(portal, TEST_USER_ID, ['Manager', 'Contributor'])
        login(portal, TEST_USER_NAME)


COLLECTIVE_DELETEPERMISSION_FIXTURE = CollectiveDeletepermissionLayer()
COLLECTIVE_DELETEPERMISSION_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(COLLECTIVE_DELETEPERMISSION_FIXTURE,),
    name="CollectiveDeletepermission:Functional")
