# -*- coding: utf-8 -*-
from senaite.referral.adapters.guards import BaseGuardAdapter
from zope.interface import implementer

from bika.lims.interfaces import IGuardAdapter


@implementer(IGuardAdapter)
class OutboundShipmentGuardAdapter(BaseGuardAdapter):

    def guard_dispatch_outbound_shipment(self):
        """Returns true if the outbound shipment can be dispatched
        """
        samples = self.context.getRawSamples()
        if not samples:
            return False
        return True
