# -*- coding: utf-8 -*-
from senaite.referral import check_installed
from senaite.referral.utils import is_from_shipment
from zope.interface import implementer

from bika.lims.interfaces import IGuardAdapter


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
        if is_from_shipment(self.context):
            return False
        return True


@implementer(IGuardAdapter)
class InboundSampleShipmentGuardAdapter(BaseGuardAdapter):

    def guard_receive_inbound_shipment(self):
        """Returns true if the inbound shipment can be fully received
        """
        samples = self.context.get_samples()
        if not samples:
            return False
        return True


@implementer(IGuardAdapter)
class OutboundSampleShipmentGuardAdapter(BaseGuardAdapter):

    def guard_dispatch(self):
        """Returns true if the outbound shipment can be dispatched
        """
        samples = self.context.get_samples()
        if not samples:
            return False
        return True
