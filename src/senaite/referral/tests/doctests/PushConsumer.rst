Push Consumer
-------------

Inbound Sample Shipments can be created remotely via POST through a
`JSONAPI's "push" custom endpoint`_. `senaite.referral` has an adapter
registered that receives POSTs on this endpoint, with the consumer name
`senaite.referral.inbound_shipment`.

Running this test from the buildout directory:

    bin/test -m senaite.referral -t PushConsumer

Test Setup
~~~~~~~~~~

Needed imports:

    >>> from datetime import datetime
    >>> import itertools
    >>> import json
    >>> import transaction
    >>> import urllib
    >>> from bika.lims import api as _api
    >>> from bika.lims.workflow import doActionFor as do_action_for
    >>> from plone.app.testing import setRoles
    >>> from plone.app.testing import TEST_USER_ID
    >>> from senaite.referral.tests import utils
    >>> from six.moves.urllib import parse

Variables:

    >>> portal = self.portal
    >>> portal_url = portal.absolute_url()
    >>> api_url = "{}/@@API/senaite/v1".format(portal_url)
    >>> browser = self.getBrowser()
    >>> setRoles(portal, TEST_USER_ID, ["LabManager", "Manager"])
    >>> transaction.commit()

Functional Helpers:

    >>> def post(url, data):
    ...     url = "{}/{}".format(api_url, url)
    ...     browser.post(url, parse.urlencode(data, doseq=True))
    ...     return browser.contents

Create some basic objects for the test:

    >>> setRoles(portal, TEST_USER_ID, ["LabManager", "Manager"])
    >>> utils.setup_baseline_data(portal)
    >>> transaction.commit()


Send messages via push
~~~~~~~~~~~~~~~~~~~~~~~

    >>> dispatched = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    >>> payload = {
    ...     'consumer': 'senaite.referral.inbound_shipment',
    ...     'lab_code': 'EXT2',
    ...     'shipment_id': 'SHIP01',
    ...     'dispatched': dispatched,
    ...     'samples': utils.read_file("shipment_01.json"),
    ... }
    >>> post("push", payload)
    '..."success": true...'

.. Links

.. _JSONAPI's "push" custom endpoint: https://senaitejsonapi.readthedocs.io/en/latest/extend.html#push-endpoint-custom-jobs