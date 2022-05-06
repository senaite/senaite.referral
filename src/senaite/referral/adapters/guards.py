# -*- coding: utf-8 -*-
from senaite.referral import check_installed
from zope.interface import implementer
from bika.lims import api
from bika.lims.interfaces import IGuardAdapter
from bika.lims.workflow import isTransitionAllowed as is_transition_allowed


class BaseGuardAdapter(object):

    def __init__(self, context):
        self.context = context

    @check_installed(True)
    def guard(self, action):
        func_name = "guard_{}".format(action)
        func = getattr(self, func_name, None)
        if func:
            return func()

        # No guard intercept here
        return True


@implementer(IGuardAdapter)
class SampleGuardAdapter(BaseGuardAdapter):
    """Adapter for Sample guards
    """

    def guard_cancel(self):
        """Returns true if the sample was not created from a Sample Shipment
        """
        if self.context.getInboundShipment():
            return False
        return True

    def guard_ship(self):
        """Returns true if the sample can be added to a shipment. This is when
        all analyses from the sample are in unassigned status
        """
        allowed = ["unassigned"]
        analyses = self.context.getAnalyses(full_objects=True)
        valid = map(lambda an: api.get_review_status(an) in allowed, analyses)
        return all(valid)


@implementer(IGuardAdapter)
class InboundSampleShipmentGuardAdapter(BaseGuardAdapter):

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


@implementer(IGuardAdapter)
class OutboundSampleShipmentGuardAdapter(BaseGuardAdapter):

    def guard_dispatch_outbound_shipment(self):
        """Returns true if the outbound shipment can be dispatched
        """
        samples = self.context.get_samples()
        if not samples:
            return False
        return True
