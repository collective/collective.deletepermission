collective.deletepermission
===========================

The default Plone permission for deleting content does not allow to delete
content from a folder without being able to delete the folder itself.

The ``collective.deletepermission`` package introduces an additional permission
``Delete portal content``. By separating the permission ``Delete portal
content`` (I can delete this content object) from the permission ``Delete
objects`` (I can delete something IN this folder), we now can allow a
``Contributor`` to delete content he created (``Owner`` role) without letting
him delete folders and objects belonging to other users - even in a nested
environment.


How it works
------------

The ``Delete portal content`` permission is required on the object you want
to delete. On parent objects the ``Delete objects`` permission is still required.
This gives more flexibility and makes it possible for a contributor to
delete his own content but nothing else.

Example with the default permission settings (deletable by Contributor1)::

  - Rootfolder of Admin (not deletable)
    '- Document of Contributor1 (deletable)
    '- Subfolder of Admin (not deletable)
      '- Document of Contributor1 (deletable)
      '- Document of Contributor2 (not deletable)

In default Plone the same structure would look like this::

  - Rootfolder of Admin (not deletable)
    '- Document of Contributor1 (deletable)
    '- Subfolder of Admin (deletable)
      '- Document of Contributor1 (deletable)
      '- Document of Contributor2 (deletable)

This is caused by the fact that in default Plone the same permission is required
on the parent and the object. If we have two levels where we should be able to
delete some files, we always end up with the user being able to delete the
container of the second level.


Default role mappings
---------------------

The package configures the following default role mappings:

**Delete portal content** (new permission):
  - Manager
  - Site Administrator
  - Owner
  - Editor

**Delete objects** (existing Zope permission):
  - Manager
  - Site Administrator
  - Contributor
  - Editor


Implementation details
----------------------

This package uses ``collective.monkeypatcher`` to patch the following methods:

**Delete operations:**

- ``manage_delObjects`` on ``plone.dexterity.content.Container`` - checks both
  ``Delete objects`` on the parent and ``Delete portal content`` on each item
  being deleted

**Cut/Paste operations:**

- ``cb_userHasCopyOrMovePermission`` on ``OFS.CopySupport.CopySource`` - requires
  both ``Copy or Move`` and ``Delete portal content`` permissions for cutting

- ``manage_cutObjects__roles__`` on ``plone.dexterity.content.Container`` - sets
  the required permission to ``Delete objects``

- ``manage_pasteObjects__roles__`` on ``plone.dexterity.content.Container`` - sets
  the required permission to ``Delete objects``

**Copy operations:**

- ``cb_isCopyable`` on ``OFS.CopySupport.CopySource`` - ensures copying does not
  require ``Delete portal content`` (only ``Copy or Move`` is needed)

**Rename operations:**

- ``manage_renameObject`` on ``OFS.CopySupport.CopyContainer`` - allows renaming
  without requiring ``Delete portal content``

The package also customizes the ``cut``, ``rename``, and ``delete`` actions in
``portal_actions/object_buttons`` to use the appropriate permission checks.


Compatibility
-------------

- Plone 6.0 (version 2.x)
- Python 3.11+

For Plone 4.x and 5.x support, use version 1.x of this package.


Installation
------------

Add ``collective.deletepermission`` to your buildout configuration::

    [instance]
    eggs +=
        collective.deletepermission

Then install the "collective.deletepermission" add-on via the Plone control panel
or by running the Generic Setup import profile.


Upgrading from 1.x
------------------

Version 2.0 is a complete rewrite for Plone 6. When upgrading:

- Archetypes support has been removed (Dexterity only)
- The CMF skins layer has been removed
- No automatic upgrade steps are provided
- You may need to manually remove obsolete skins and actions


Links
-----

- Github: https://github.com/collective/collective.deletepermission
- Issues: https://github.com/collective/collective.deletepermission/issues
- PyPI: https://pypi.python.org/pypi/collective.deletepermission


Copyright
---------

This package is copyright by `webcloud7 <https://www.webcloud7.ch/>`_.

The original package was developed and maintained by 4teamwork (until version 1.x).

``collective.deletepermission`` is licensed under GNU General Public License,
version 2.
