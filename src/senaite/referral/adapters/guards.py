# -*- coding: utf-8 -*-
from senaite.referral import check_installed
from senaite.referral.utils import is_from_shipment
from zope.interface import implementer

from bika.lims.interfaces import IGuardAdapter


@implementer(IGuardAdapter)
class SampleGuardAdapter(object):
    """Adapter for Sample guards
    """

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

    def guard_cancel(self):
        """Returns true if the sample was not created from a Sample Shipment
        """
        if is_from_shipment(self.context):
            return False
        return True
