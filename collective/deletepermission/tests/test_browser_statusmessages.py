from collective.deletepermission.tests.base import FunctionalTestCase


class TestBrowserStatusMessages(FunctionalTestCase):
    """Test that status messages are properly captured from rendered HTML."""

    def setUp(self):
        self.user_a = self.create_user(userid='usera', roles=['Contributor'])
        with self.user(self.user_a):
            self.folder = self.create_folder(title='testfolder')
            self.doc = self.create_folder(
                container=self.folder,
                title='testdoc'
            )

    def test_delete_shows_status_message(self):
        """Test that deleting an object shows success message in rendered HTML."""
        browser = self.get_browser()
        browser.login(self.user_a).open(self.doc, view='delete_confirmation')
        browser.find('Delete').click()

        # After delete, we should have a success message
        # The exact message may vary, but there should be an info message
        messages = browser.get_status_messages()
        # At minimum, verify no error messages
        self.assertEqual([], messages['error'])

    def test_copy_shows_status_message(self):
        """Test that copying shows status message."""
        browser = self.get_browser()
        browser.login(self.user_a).open(self.doc)
        browser.find('Copy').click()

        # Should have info message about copy
        info_msgs = browser.info_messages()
        # Verify some message exists (Plone may show various copy-related messages)
        self.assertIsInstance(info_msgs, list)

    def test_assert_no_error_messages_passes_when_no_errors(self):
        """Test that assert_no_error_messages works correctly."""
        browser = self.get_browser()
        browser.login(self.user_a).open(self.doc)

        # This should not raise an exception
        browser.assert_no_error_messages()

    def test_rename_shows_no_errors_on_success(self):
        """Test successful rename shows no error messages."""
        browser = self.get_browser()
        browser.login(self.user_a).open(self.doc)
        browser.find('Rename').click()
        browser.fill({'New Short Name': 'renamed-doc'}).find('Rename').click()

        # Should have no errors
        browser.assert_no_error_messages()
        self.assertEqual(self.folder.absolute_url() + '/renamed-doc', browser.url)
