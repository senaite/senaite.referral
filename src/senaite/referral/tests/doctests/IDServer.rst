ID Server
---------

Senaite referral enables ID server to support additional wildcards for ID
generation, as well as additional formatting for samples that are created from
inbound shipments.

Running this test from the buildout directory:

    bin/test -m senaite.referral -t IDServer

Test Setup
~~~~~~~~~~

Needed imports:

    >>> from bika.lims import api
    >>> from bika.lims.workflow import doActionFor as do_action_for
    >>> from datetime import datetime
    >>> from datetime import timedelta
    >>> from plone.app.testing import setRoles
    >>> from plone.app.testing import TEST_USER_ID
    >>> from senaite.referral.setuphandlers import setup_id_formatting
    >>> from senaite.referral.tests import utils

Variables:

    >>> portal = self.portal

Create some basic objects for the test:

    >>> setRoles(portal, TEST_USER_ID, ["LabManager", "Manager"])
    >>> utils.setup_baseline_data(portal)
    >>> labs = portal.external_labs.objectValues()
    >>> clients = portal.clients.objectValues()


Additional wildcard for InboundShipment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

SENAITE referral adds the code of the referring laboratory as a variable
`lab_code` on `InboundSampleShipmen` objects creation. This code can be used as
a wildcard in the formatting record for objects of this portal type.

Update the formatting configuration for InboundSampleShipments:

    >>> format_definition = {
    ...     "portal_type": "InboundSampleShipment",
    ...     "form": "{lab_code}-IN-{seq:02d}",
    ...     "prefix": "inboundsampleshipment",
    ...     "sequence_type": "generated",
    ...     "counter_type": "",
    ...     "split_length": 2,
    ... }
    >>> setup_id_formatting(portal, format_definition=format_definition)

Manually create an inbound shipment (note that in real life, inbound
shipments are created through a push consumer - see PushConsumer.rst):

    >>> lab = filter(lambda lab: lab.code == "EXT2", labs)[0]
    >>> client = filter(lambda cl: cl.getClientID() == "HH", clients)[0]
    >>> values = {
    ...     "referring_laboratory": api.get_uid(lab),
    ...     "referring_client": api.get_uid(client),
    ...     "comments": "Test inbound sample shipment",
    ...     "dispatched_datetime": datetime.now() - timedelta(days=2)
    ... }
    >>> shipment = api.create(lab, "InboundSampleShipment", **values)
    >>> api.get_id(shipment)
    'EXT2-IN-01'

Let's create another one:

    >>> shipment = api.create(lab, "InboundSampleShipment", **values)
    >>> api.get_id(shipment)
    'EXT2-IN-02'

Create another shipment, but from another external laboratory:

    >>> lab = filter(lambda lab: lab.code == "EXT3", labs)[0]
    >>> values.update({
    ...     "referring_laboratory": api.get_uid(lab),
    ... })
    >>> shipment = api.create(lab, "InboundSampleShipment", **values)
    >>> api.get_id(shipment)
    'EXT3-IN-01'


Additional wildcard for OutboundShipment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

SENAITE referral adds the code of the current laboratory as a variable
`lab_code` on `OutboundSampleShipment` objects creation. This code can be used
as a wildcard in the formatting record for objects of this portal type.

Update the formatting configuration for `OutboundSampleShipment`:

    >>> format_definition = {
    ...     "portal_type": "OutboundSampleShipment",
    ...     "form": "{lab_code}-OUT-{seq:02d}",
    ...     "prefix": "outboundsampleshipment",
    ...     "sequence_type": "generated",
    ...     "counter_type": "",
    ...     "split_length": 2,
    ... }
    >>> setup_id_formatting(portal, format_definition=format_definition)

Manually create an outbound shipment:

    >>> lab = filter(lambda lab: lab.code == "EXT2", labs)[0]
    >>> values = {"comments": "Test outbound shipment"}
    >>> shipment = api.create(lab, "OutboundSampleShipment", **values)
    >>> api.get_id(shipment)
    'EXT2-OUT-01'

Let's create another one:

    >>> shipment = api.create(lab, "OutboundSampleShipment", **values)
    >>> api.get_id(shipment)
    'EXT2-OUT-02'

Create another shipment, but to another external laboratory:

    >>> lab = filter(lambda lab: lab.code == "EXT3", labs)[0]
    >>> shipment = api.create(lab, "OutboundSampleShipment", **values)
    >>> api.get_id(shipment)
    'EXT3-OUT-01'

Additional wildcard for incoming samples
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `lab_code` wildcard is also available for Samples that are created
automatically as per inbound sample shipments reception. The value of the
variable is the laboratory code of the referring laboratory. For thist to be
possible, a new idserver-specific type id exists: `AnalysisRequestFromShipment`

Update the formatting configuration for this "virtual" type:

    >>> format_definition = {
    ...     "portal_type": "AnalysisRequestFromShipment",
    ...     "form": "{lab_code}-SHIP-{seq:02d}",
    ...     "prefix": "analysisrequestfromshipment",
    ...     "sequence_type": "generated",
    ...     "counter_type": "",
    ...     "split_length": 2,
    ... }
    >>> setup_id_formatting(portal, format_definition=format_definition)

Manually create an inbound shipment (note that in real life, inbound
shipments are created through a push consumer - see PushConsumer.rst):

    >>> lab = filter(lambda lab: lab.code == "EXT2", labs)[0]
    >>> client = filter(lambda cl: cl.getClientID() == "HH", clients)[0]
    >>> values = {
    ...     "referring_laboratory": api.get_uid(lab),
    ...     "referring_client": api.get_uid(client),
    ...     "comments": "Test inbound sample shipment",
    ...     "dispatched_datetime": datetime.now() - timedelta(days=2)
    ... }
    >>> shipment = api.create(lab, "InboundSampleShipment", **values)

Create an `InboundSample` object and receive:

    >>> values = {
    ...     "referring_id": "000001",
    ...     "date_sampled": datetime.now() - timedelta(days=5),
    ...     "sample_type": "Water",
    ...     "analyses": ["Cu", "Fe"],
    ... }
    >>> inbound_sample = api.create(shipment, "InboundSample", **values)
    >>> success = do_action_for(inbound_sample, "receive_inbound_sample")

A new "regular" sample has been created, but with a custom ID:

    >>> sample = shipment.getSamples()[0]
    >>> api.get_id(sample)
    'EXT2-SHIP-01'
