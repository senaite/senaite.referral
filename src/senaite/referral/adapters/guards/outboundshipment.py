# -*- coding: utf-8 -*-
from senaite.referral.adapters.guards import BaseGuardAdapter
from zope.interface import implementer

from bika.lims.interfaces import IGuardAdapter


@implementer(IGuardAdapter)
class OutboundShipmentGuardAdapter(BaseGuardAdapter):

    def has_samples(self, shipment):
        """Returns whether the shipment passed-in has samples or not
        """
        if not shipment.getRawSamples():
            return False
        return True

    def guard_dispatch_outbound_shipment(self):
        """Returns true if the outbound shipment can be dispatched
        """
        if not self.has_samples(self.context):
            return False

        if not self.context.getManifest():
            # Cannot dispatch unless the shipment manifest is present
            return False

        return True

    def guard_finalise_outbound_shipment(self):
        """Returns true if the outbound shipment contains at least one sample
        """
        return self.has_samples(self.context)
