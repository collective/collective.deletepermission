from setuptools import setup

import os

version = "2.0.0a1"

tests_require = [
    "AccessControl",
    "Products.CMFCore",
    "Products.GenericSetup",
    "Products.statusmessages",
    "Zope",
    "beautifulsoup4",
    "requests",
    "plone.api >= 1.3.0",
    "plone.app.contenttypes",
    "plone.app.dexterity",
    "plone.app.portlets",
    "plone.app.testing",
    "plone.autoform",
    "transaction",
    "zExceptions",
    "zope.interface",
]


extras_require = {
    "test": tests_require,
}


long_description = (
    open("README.rst", encoding="utf-8").read()
    + "\n"
    + open(os.path.join("docs", "HISTORY.txt"), encoding="utf-8").read()
    + "\n"
)

setup(
    name="collective.deletepermission",
    version=version,
    description="Implements a new permission 'Delete portal content'",
    long_description=long_description,
    # Get more strings from
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Framework :: Plone",
        "Framework :: Plone :: 6.1",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.11",
    keywords="collective deletepermission webcloud7 plone",
    author="Mathias Leimgruber (webcloud7 ag)",
    author_email="mailto:m.leimgruber@webcloud7.ch",
    url="https://github.com/colletive/collective.deletepermission",
    license="GPL2",
    packages=[
        "collective.deletepermission",
        "collective.deletepermission.tests",
        "collective.deletepermission.upgrades",
    ],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "AccessControl",
        "Acquisition",
        "Products.CMFCore",
        "Products.CMFPlone",
        "Products.GenericSetup",
        "Products.PythonScripts",
        "ZODB",
        "Zope",
        "collective.monkeypatcher",
        "setuptools",
        "zope.container",
        "zope.event",
        "zope.lifecycleevent",
    ],
    extras_require=extras_require,
    entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
)
