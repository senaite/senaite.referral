# -*- coding: utf-8 -*-
from senaite.referral.adapters.guards import BaseGuardAdapter
from zope.interface import implementer

from bika.lims import api
from bika.lims.interfaces import IGuardAdapter
from bika.lims.workflow import isTransitionAllowed as is_transition_allowed


@implementer(IGuardAdapter)
class InboundShipmentGuardAdapter(BaseGuardAdapter):

    def guard_receive_inbound_shipment(self):
        """Returns true if the inbound shipment contains at least one inbound
        sample and all its inbound samples can either be received or have been
        received already
        """
        samples = self.context.getInboundSamples()
        if not samples:
            return False

        action_id = "receive_inbound_sample"
        for inbound_sample in samples:
            if api.get_review_status(inbound_sample) == "received":
                continue
            if not is_transition_allowed(inbound_sample, action_id):
                return False
        return True
