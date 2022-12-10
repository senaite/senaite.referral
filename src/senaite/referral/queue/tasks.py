# -*- coding: utf-8 -*-

from bika.lims import api
from bika.lims.utils.analysisrequest import create_analysisrequest
from bika.lims.workflow import doActionFor

from senaite.queue.interfaces import IQueuedTaskAdapter
from senaite.referral import logger
from senaite.referral.interfaces import IInboundSample
from senaite.referral.workflow.inboundsample.events import get_new_sample_info
from zope.component import adapter
from zope.interface import implementer


@implementer(IQueuedTaskAdapter)
@adapter(IInboundSample)
class CreateSampleFromInboundSampleAdapter(object):
    """Adapter for the creation of the sample counterpart of an inbound sample
    """

    def __init__(self, context):
        self.context = context

    def process(self, task):
        """Transition the objects from the task
        """
        # Do nothing if it has a 'real' sample assigned already
        if self.context.getRawSample():
            path = api.get_path(self.context)
            logger.warn("Inbound sample with a Sample assigned already: {}"
                        .format(path))
            return True

        # Extract the data to assign to the 'new' sample
        values = task.get("data", None)
        if not values:
            logger.warn("No 'data' payload")
            values = get_new_sample_info(self.context)
            task.update({"data": values})

        # Create the sample
        client = values.pop("Client")
        client = api.get_object_by_uid(client)
        services = values.pop("analyses")
        request = api.get_request()
        sample = create_analysisrequest(client, request, values, services)

        # Associate this new Sample with the Inbound Sample
        self.context.setSample(sample)

        # Auto-receive the sample object
        doActionFor(sample, "receive")

        # Try to to receive the whole shipment
        shipment = sample.getInboundShipment()
        doActionFor(shipment, "receive_inbound_shipment")

        return True
