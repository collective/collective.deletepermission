from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.SecurityManagement import setSecurityManager
from bs4 import BeautifulSoup
from collective.deletepermission import testing
from contextlib import contextmanager
from plone import api
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from unittest import TestCase
from urllib.parse import urlparse
from zExceptions import Unauthorized
import base64
import requests
import transaction


class TestBrowser:
    """Simple browser implementation using HTTP requests."""

    def __init__(self, layer):
        self.layer = layer
        self.portal = layer['portal']
        self.app = layer['app']
        self._current_user = None
        self._current_password = None
        self._last_response = None
        self._last_url = None
        self._last_html = None
        self._soup = None
        self.session = requests.Session()
        # Get the base URL for the portal
        self.base_url = self.portal.absolute_url()

    def _get_auth_headers(self):
        """Build authentication headers for HTTP requests."""
        headers = {}
        if self._current_user:
            password = self._current_password or self._current_user
            auth_string = f"{self._current_user}:{password}".encode('utf-8')
            auth_header = base64.b64encode(auth_string).decode('ascii')
            headers['Authorization'] = f'Basic {auth_header}'
        return headers

    def login(self, username=TEST_USER_NAME, password=None):
        """Login as user."""
        if hasattr(username, 'id'):
            username = username.id
        elif hasattr(username, 'getUserName'):
            username = username.getUserName()

        # For created test users, password is {userid}{userid}
        # For TEST_USER, password is TEST_USER_PASSWORD
        if password is None:
            if username == TEST_USER_NAME:
                password = TEST_USER_PASSWORD
            else:
                password = f'{username}{username}'

        # Login via Zope security machinery
        login(self.portal, username)
        self._current_user = username
        self._current_password = password
        self.session.headers.update(self._get_auth_headers())

        return self

    def logout(self):
        """Logout current user."""
        logout()
        self._current_user = None
        self._current_password = None
        self.session.headers.pop('Authorization', None)
        return self

    def open(self, obj, view=None):
        """Open an object and render its view via HTTP request."""
        if view:
            url = f"{obj.absolute_url()}/{view}"
        else:
            url = obj.absolute_url()
        self._last_url = url
        self._last_obj = obj
        self._last_view = view

        # Make HTTP request to get HTML
        try:
            headers = self._get_auth_headers()
            response = self.session.get(url, headers=headers)
            self._last_response = response

            # Check if we got unauthorized or forbidden
            if response.status_code in [401, 403]:
                raise Unauthorized("Unauthorized access")

            self._last_html = response.text

            # Check for Plone's Insufficient Privileges page
            if self._is_unauthorized_response(self._last_html):
                raise Unauthorized("Unauthorized access")

            # Parse HTML with BeautifulSoup
            if self._last_html:
                self._soup = BeautifulSoup(self._last_html, 'html.parser')
        except requests.RequestException as e:
            # Request failed, that's ok for some tests
            self._last_html = None
            self._soup = None

        return self

    def visit(self, obj, view=None):
        """Alias for open."""
        return self.open(obj, view)

    def _is_unauthorized_response(self, response_text, debug=False):
        """Check if response indicates unauthorized access."""
        # Look for specific error page indicators
        soup = BeautifulSoup(response_text, 'html.parser')
        # Check for Plone error page - h1 with class documentFirstHeading containing error text
        h1 = soup.find('h1', class_='documentFirstHeading')
        if h1:
            h1_text = h1.get_text()
            if debug:
                print(f"DEBUG: h1 text = '{h1_text}'")
            if 'Insufficient Privileges' in h1_text:
                return True
            # Also check for login required page
            if 'Login' in h1_text and 'require_login' in response_text:
                return True
        return False

    def cut(self):
        """Cut the current object via direct view call."""
        if not self._last_obj:
            raise ValueError("No object to cut")

        view_url = f"{self._last_obj.absolute_url()}/object_cut"

        try:
            headers = self._get_auth_headers()
            response = self.session.get(view_url, headers=headers, allow_redirects=True)

            # Update browser to show parent after action
            self._last_response = response
            self._last_url = response.url
            self._last_html = response.text

            # Check for unauthorized - but only by status code, not content
            if response.status_code in [401, 403]:
                raise Unauthorized("Unauthorized access")

            if self._last_html:
                self._soup = BeautifulSoup(self._last_html, 'html.parser')
        except requests.RequestException:
            pass

        return self

    def copy(self):
        """Copy the current object via direct view call."""
        if not self._last_obj:
            raise ValueError("No object to copy")

        view_url = f"{self._last_obj.absolute_url()}/object_copy"

        try:
            headers = self._get_auth_headers()
            response = self.session.get(view_url, headers=headers, allow_redirects=True)

            # Update browser state
            self._last_response = response
            self._last_url = response.url
            self._last_html = response.text

            # Check for unauthorized - but only by status code, not content
            if response.status_code in [401, 403]:
                raise Unauthorized("Unauthorized access")

            if self._last_html:
                self._soup = BeautifulSoup(self._last_html, 'html.parser')
        except requests.RequestException:
            pass

        return self

    def delete(self):
        """Delete the current object by submitting the delete form."""
        if not self._last_obj:
            raise ValueError("No object to delete")

        action = f"{self._last_obj.absolute_url()}/delete_confirmation"
        headers = self._get_auth_headers()

        try:
            # First GET the form to obtain CSRF token and check permission
            get_response = self.session.get(action, headers=headers)
            if get_response.status_code in [401, 403]:
                raise Unauthorized("Unauthorized access")
            if self._is_unauthorized_response(get_response.text):
                raise Unauthorized("Unauthorized access")

            # Parse form to get authenticator token
            soup = BeautifulSoup(get_response.text, 'html.parser')
            authenticator = None
            auth_input = soup.find('input', {'name': '_authenticator'})
            if auth_input:
                authenticator = auth_input.get('value')

            # Plone 6 uses z3c.form - button is form.buttons.Delete
            form_data = {
                'form.buttons.Delete': 'Delete',
            }
            if authenticator:
                form_data['_authenticator'] = authenticator

            response = self.session.post(action, data=form_data, headers=headers, allow_redirects=True)
            self._last_response = response

            # Check for unauthorized or forbidden
            if response.status_code in [401, 403]:
                raise Unauthorized("Unauthorized access")

            # Update browser state with response
            self._last_url = response.url
            self._last_html = response.text

            # Check for Plone's Insufficient Privileges page
            if self._is_unauthorized_response(self._last_html):
                raise Unauthorized("Unauthorized access")

            if self._last_html:
                self._soup = BeautifulSoup(self._last_html, 'html.parser')

            # Update to parent object after delete
            if response.url:
                parsed = urlparse(response.url)
                path = parsed.path
                portal_path = urlparse(self.base_url).path
                if path.startswith(portal_path):
                    path = path[len(portal_path):]
                if path.startswith('/'):
                    path = path[1:]

                if path:
                    try:
                        self._last_obj = self.portal.restrictedTraverse(path)
                    except (KeyError, AttributeError):
                        pass

        except requests.RequestException:
            pass

        return self

    def rename(self, new_id):
        """Rename the current object via HTTP request to object_rename view."""
        if not self._last_obj:
            raise ValueError("No object to rename")

        # Use object_rename view directly
        action = f"{self._last_obj.absolute_url()}/object_rename"
        headers = self._get_auth_headers()

        try:
            # First GET the form to obtain CSRF token
            get_response = self.session.get(action, headers=headers)
            if get_response.status_code in [401, 403]:
                raise Unauthorized("Unauthorized access")
            if self._is_unauthorized_response(get_response.text):
                raise Unauthorized("Unauthorized access")

            # Parse form to get authenticator token
            soup = BeautifulSoup(get_response.text, 'html.parser')
            authenticator = None
            auth_input = soup.find('input', {'name': '_authenticator'})
            if auth_input:
                authenticator = auth_input.get('value')

            # Plone 6 uses z3c.form - field names are form.widgets.FIELDNAME
            form_data = {
                'form.widgets.new_id': new_id,
                'form.widgets.new_title': new_id,  # Use same as id if no specific title
                'form.buttons.Rename': 'Rename',
            }
            if authenticator:
                form_data['_authenticator'] = authenticator

            response = self.session.post(action, data=form_data, headers=headers, allow_redirects=True)
            self._last_response = response

            # Check for unauthorized or forbidden
            if response.status_code in [401, 403]:
                raise Unauthorized("Unauthorized access")

            # Update browser state
            self._last_url = response.url
            self._last_html = response.text

            # Check for Plone's Insufficient Privileges page
            if self._is_unauthorized_response(self._last_html):
                raise Unauthorized("Unauthorized access")

            if self._last_html:
                self._soup = BeautifulSoup(self._last_html, 'html.parser')

            # Update object reference
            if response.url:
                parsed = urlparse(response.url)
                path = parsed.path
                portal_path = urlparse(self.base_url).path
                if path.startswith(portal_path):
                    path = path[len(portal_path):]
                if path.startswith('/'):
                    path = path[1:]

                if path:
                    try:
                        self._last_obj = self.portal.restrictedTraverse(path)
                    except (KeyError, AttributeError):
                        pass

        except requests.RequestException:
            pass

        return self

    @contextmanager
    def expect_unauthorized(self):
        """Context manager to expect Unauthorized exception."""
        try:
            yield
            raise AssertionError("Expected Unauthorized exception was not raised")
        except Unauthorized:
            # This is expected
            pass

    @property
    def url(self):
        """Return current URL."""
        return self._last_url

    def get_status_messages(self):
        """Extract status messages from the rendered HTML."""
        messages = {
            'info': [],
            'warning': [],
            'error': []
        }

        if not self._soup:
            return messages

        # Find status messages in the DOM
        # Plone 6 uses dl.portalMessage structure
        for msg_container in self._soup.find_all('dl', class_='portalMessage'):
            # Get message type from class
            msg_type = None
            if 'info' in msg_container.get('class', []):
                msg_type = 'info'
            elif 'warning' in msg_container.get('class', []):
                msg_type = 'warning'
            elif 'error' in msg_container.get('class', []):
                msg_type = 'error'

            # Get message text
            dd = msg_container.find('dd')
            if dd and msg_type:
                messages[msg_type].append(dd.get_text(strip=True))

        # Also check for newer alert-based messages
        for alert in self._soup.find_all('div', class_='alert'):
            msg_text = alert.get_text(strip=True)
            if 'alert-info' in alert.get('class', []):
                messages['info'].append(msg_text)
            elif 'alert-warning' in alert.get('class', []):
                messages['warning'].append(msg_text)
            elif 'alert-danger' in alert.get('class', []) or 'alert-error' in alert.get('class', []):
                messages['error'].append(msg_text)

        return messages

    def info_messages(self):
        """Get info status messages."""
        return self.get_status_messages()['info']

    def warning_messages(self):
        """Get warning status messages."""
        return self.get_status_messages()['warning']

    def error_messages(self):
        """Get error status messages."""
        return self.get_status_messages()['error']

    def assert_no_error_messages(self):
        """Assert there are no error messages."""
        errors = self.error_messages()
        if errors:
            raise AssertionError(f"Expected no error messages, but got: {errors}")


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

    def get_browser(self):
        """Create and return a TestBrowser instance."""
        if not hasattr(self, '_browser'):
            self._browser = TestBrowser(self.layer)
        return self._browser

    def get_actions(self):
        """Get available actions for the current context."""
        # Get actions from the content menu
        if not hasattr(self, '_browser') or not hasattr(self._browser, '_last_obj'):
            return []

        obj = self._browser._last_obj
        context_state = obj.restrictedTraverse('@@plone_context_state')
        actions = context_state.actions('object_buttons')

        return [action['title'] for action in actions]

    def get_status_messages(self):
        """Get status messages from the current browser view."""
        if hasattr(self, '_browser') and self._browser:
            return self._browser.get_status_messages()
        return {'info': [], 'warning': [], 'error': []}

    def assert_no_error_messages(self):
        """Assert there are no error messages in the current browser view."""
        if hasattr(self, '_browser') and self._browser:
            self._browser.assert_no_error_messages()

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

        # Set password for HTTP Basic Auth in tests (min 8 chars required)
        password = f'{userid}{userid}'
        user = api.user.create(
            email=email,
            username=userid,
            password=password,
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
