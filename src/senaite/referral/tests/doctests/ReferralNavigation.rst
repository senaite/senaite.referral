Referral Navigation Bar Visibility
===================================

This test ensures that the Shipments and External Labs folders are visible in
the navigation bar after installation, in accordance with the new sidebar
navigation system introduced in senaite.core.

Running this test from the buildout directory:

    bin/test -m senaite.referral -t ReferralNavigation


Test Setup
..........

Needed Imports:

    >>> from bika.lims import api
    >>> from plone.app.testing import setRoles
    >>> from plone.app.testing import TEST_USER_ID

Variables:

    >>> portal = self.portal
    >>> request = self.request
    >>> setup = api.get_senaite_setup()

Assign default roles for the user to test with:

    >>> setRoles(portal, TEST_USER_ID, ['LabManager',])


Shipments Folder Navigation Visibility
---------------------------------------

After installation, the Shipments folder should be visible in the navigation
bar. This is configured through two mechanisms:

1. The portal type "ShipmentFolder" should NOT be in SENAITE Setup's
   sidebar_skip_types (types in this list are excluded from the sidebar):

    >>> sidebar_skip_types = setup.getSidebarSkipTypes()
    >>> sidebar_skip_types is not None
    True
    >>> "ShipmentFolder" not in sidebar_skip_types
    True

2. Since the shipments folder is a root folder (direct child of portal), its
   ID should be in SENAITE Setup's sidebar_folders:

    >>> sidebar_folders = setup.getSidebarFolders()
    >>> sidebar_folders is not None
    True
    >>> "shipments" in sidebar_folders
    True

Verify the shipments folder exists and is properly configured:

    >>> shipments = portal.shipments
    >>> shipments is not None
    True

    >>> api.get_portal_type(shipments)
    'ShipmentFolder'

    >>> api.get_parent(shipments) == portal
    True


External Labs Folder Navigation Visibility
--------------------------------------------

After installation, the External Labs folder should be visible in the
navigation bar:

1. The portal type "ExternalLaboratoryFolder" should NOT be in SENAITE Setup's
   sidebar_skip_types:

    >>> "ExternalLaboratoryFolder" not in sidebar_skip_types
    True

2. Since the external_labs folder is a root folder, its ID should be in
   SENAITE Setup's sidebar_folders:

    >>> "external_labs" in sidebar_folders
    True

Verify the external_labs folder exists and is properly configured:

    >>> external_labs = portal.external_labs
    >>> external_labs is not None
    True

    >>> api.get_portal_type(external_labs)
    'ExternalLaboratoryFolder'

    >>> api.get_parent(external_labs) == portal
    True
