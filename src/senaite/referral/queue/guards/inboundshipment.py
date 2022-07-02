# -*- coding: utf-8 -*-

from senaite.queue import api as qapi
from senaite.referral.queue import is_under_consumption
from zope.interface import implementer

from bika.lims.interfaces import IGuardAdapter


@implementer(IGuardAdapter)
class InboundShipmentGuardAdapter(object):

    def __init__(self, context):
        self.context = context

    def guard(self, action):
        """Returns False if the inbound shipment, or any of its inbound samples
        is being processed by the queue
        """
        if is_under_consumption(self.context):
            # Let the consumer perform the transition if necessary
            return True

        # Check if the shipment is queued
        if qapi.is_queued(self.context):
            return False

        # Check whether the shipment contains queued samples
        for sample in self.context.getInboundSamples():
            if qapi.is_queued(sample):
                return False

        return True
