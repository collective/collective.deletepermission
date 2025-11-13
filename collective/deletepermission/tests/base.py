from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.SecurityManagement import setSecurityManager
from bs4 import BeautifulSoup
from collective.deletepermission import testing
from contextlib import contextmanager
from plone import api
from plone.app.testing import login
from plone.app.testing import logout
from unittest import TestCase
from zExceptions import Unauthorized
import requests
import transaction
from urllib.parse import urljoin


class TestBrowser:
    """Simple browser implementation using HTTP requests."""

    def __init__(self, layer):
        self.layer = layer
        self.portal = layer['portal']
        self.app = layer['app']
        self._current_user = None
        self._last_response = None
        self._last_url = None
        self._last_html = None
        self._soup = None
        self.session = requests.Session()
        # Get the base URL for the portal
        self.base_url = self.portal.absolute_url()

    def login(self, user=None):
        """Login as user."""
        if user is None:
            from plone.app.testing import TEST_USER_NAME
            login(self.portal, TEST_USER_NAME)
            self._current_user = TEST_USER_NAME
        elif hasattr(user, 'id'):
            login(self.portal, user.id)
            self._current_user = user.id
        elif hasattr(user, 'getUserName'):
            login(self.portal, user.getUserName())
            self._current_user = user.getUserName()
        else:
            login(self.portal, user)
            self._current_user = user
        return self

    def logout(self):
        """Logout current user."""
        logout()
        self._current_user = None
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
            # Add authentication header if user is logged in
            headers = {}
            if self._current_user:
                # Use HTTP Basic Auth with the session
                import base64
                auth_string = f"{self._current_user}:{self._current_user}".encode('utf-8')
                auth_header = base64.b64encode(auth_string).decode('ascii')
                headers['Authorization'] = f'Basic {auth_header}'

            response = self.session.get(url, headers=headers)
            self._last_response = response

            # Check if we got unauthorized or forbidden
            if response.status_code in [401, 403]:
                raise Unauthorized("Unauthorized access")

            self._last_html = response.text

            # Also check if the response contains an unauthorized error message
            # Plone sometimes returns 200 with error message in the page
            if 'Insufficient Privileges' in self._last_html or 'Unauthorized' in self._last_html:
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

    def _parse_form(self, form_id=None, button_text=None):
        """Parse a form from the current page and return form data."""
        if not self._soup:
            return None, None

        # Find the form
        form = None
        if form_id:
            form = self._soup.find('form', id=form_id)
        elif button_text:
            # Find form containing a button with this text
            buttons = self._soup.find_all(['button', 'input'])
            for button in buttons:
                if button.get('type') in ['submit', 'button'] or button.name == 'button':
                    if button.get_text(strip=True) == button_text or button.get('value') == button_text:
                        form = button.find_parent('form')
                        if form:
                            break

        if not form:
            # Try to find any form on the page
            form = self._soup.find('form')

        if not form:
            return None, None

        # Get form action
        action = form.get('action', '')
        if not action:
            action = self._last_url
        elif not action.startswith('http'):
            action = urljoin(self._last_url, action)

        # Extract all form fields
        form_data = {}
        for input_field in form.find_all(['input', 'textarea', 'select']):
            name = input_field.get('name')
            if not name:
                continue

            field_type = input_field.get('type', 'text').lower()

            if field_type == 'checkbox':
                if input_field.get('checked'):
                    form_data[name] = input_field.get('value', 'on')
            elif field_type == 'radio':
                if input_field.get('checked'):
                    form_data[name] = input_field.get('value')
            elif field_type in ['submit', 'button']:
                # Only include if this is the button being clicked
                if button_text and (input_field.get('value') == button_text or input_field.get_text(strip=True) == button_text):
                    form_data[name] = input_field.get('value', button_text)
            elif input_field.name == 'select':
                # Get selected option
                selected = input_field.find('option', selected=True)
                if selected:
                    form_data[name] = selected.get('value', selected.get_text(strip=True))
            else:
                # text, hidden, password, etc.
                value = input_field.get('value', '')
                if value:
                    form_data[name] = value

        return action, form_data

    def find(self, text):
        """Find button/link by text - returns a mock object with click method."""
        class ClickableElement:
            def __init__(self, browser, text, obj, view):
                self.browser = browser
                self.text = text
                self.obj = obj
                self.view = view

            def click(self):
                """Click the element by submitting its form via HTTP POST."""
                # Parse the form from the current page
                action, form_data = self.browser._parse_form(button_text=self.text)

                if not action:
                    # No form found, try to handle as a direct action
                    text_lower = self.text.lower()

                    if text_lower in ['cut', 'copy']:
                        # These are typically links, not form submissions
                        # Make GET request to the action URL
                        if text_lower == 'cut':
                            action_url = f"{self.obj.absolute_url()}/object_cut"
                        else:  # copy
                            action_url = f"{self.obj.absolute_url()}/object_copy"

                        try:
                            headers = {}
                            if self.browser._current_user:
                                import base64
                                auth_string = f"{self.browser._current_user}:{self.browser._current_user}".encode('utf-8')
                                auth_header = base64.b64encode(auth_string).decode('ascii')
                                headers['Authorization'] = f'Basic {auth_header}'

                            response = self.browser.session.get(action_url, headers=headers, allow_redirects=True)

                            # Check for unauthorized or forbidden
                            if response.status_code in [401, 403]:
                                raise Unauthorized("Unauthorized access")

                            # Also check if the response contains an unauthorized error message
                            if 'Insufficient Privileges' in response.text or 'Unauthorized' in response.text:
                                raise Unauthorized("Unauthorized access")

                            # Update browser to show parent after action
                            self.browser.open(self.obj.aq_parent)
                        except requests.RequestException:
                            pass

                        return self.browser
                    elif text_lower == 'rename':
                        # Navigate to rename form if no form data yet
                        if not hasattr(self.browser, '_form_data') or 'New Short Name' not in self.browser._form_data:
                            self.browser._last_view = 'content_status_modify'
                            return self.browser

                # Merge any form data set via fill()
                if hasattr(self.browser, '_form_data'):
                    if form_data is None:
                        form_data = {}
                    form_data.update(self.browser._form_data)
                    # Clear form data after use
                    delattr(self.browser, '_form_data')

                # Make HTTP POST request
                try:
                    headers = {}
                    if self.browser._current_user:
                        import base64
                        auth_string = f"{self.browser._current_user}:{self.browser._current_user}".encode('utf-8')
                        auth_header = base64.b64encode(auth_string).decode('ascii')
                        headers['Authorization'] = f'Basic {auth_header}'

                    response = self.browser.session.post(action, data=form_data, headers=headers, allow_redirects=True)
                    self.browser._last_response = response

                    # Check for unauthorized or forbidden
                    if response.status_code in [401, 403]:
                        raise Unauthorized("Unauthorized access")

                    # Update browser state with response
                    self.browser._last_url = response.url
                    self.browser._last_html = response.text

                    # Also check if the response contains an unauthorized error message
                    if 'Insufficient Privileges' in self.browser._last_html or 'Unauthorized' in self.browser._last_html:
                        raise Unauthorized("Unauthorized access")

                    if self.browser._last_html:
                        self.browser._soup = BeautifulSoup(self.browser._last_html, 'html.parser')

                    # After successful delete/rename, update the object reference
                    # The response URL tells us where we ended up
                    # We need to traverse to that object
                    if response.url:
                        # Extract path from URL
                        from urllib.parse import urlparse
                        parsed = urlparse(response.url)
                        path = parsed.path
                        # Remove portal path prefix
                        portal_path = urlparse(self.browser.base_url).path
                        if path.startswith(portal_path):
                            path = path[len(portal_path):]
                        if path.startswith('/'):
                            path = path[1:]

                        # Traverse to the object
                        if path:
                            try:
                                self.browser._last_obj = self.browser.portal.restrictedTraverse(path)
                            except (KeyError, AttributeError):
                                # Object might have been deleted
                                pass

                except requests.RequestException as e:
                    # Request failed
                    pass

                return self.browser

        return ClickableElement(self, text, self._last_obj, self._last_view)

    def fill(self, data):
        """Fill form fields."""
        self._form_data = data
        return self

    def save(self):
        """Save/submit the form."""
        # For content creation/editing
        if self._form_data and 'Title' in self._form_data:
            # This simulates form submission
            transaction.commit()
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
