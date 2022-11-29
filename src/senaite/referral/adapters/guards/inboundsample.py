# -*- coding: utf-8 -*-
from senaite.referral.adapters.guards import BaseGuardAdapter
from zope.interface import implementer

from bika.lims.interfaces import IGuardAdapter


@implementer(IGuardAdapter)
class InboundSampleGuardAdapter(BaseGuardAdapter):

    def guard_receive__inbound_sample(self):
        """Returns true if the inbound sample can be received, either because
        is in a suitable status (due) or because it is received, but without
        a sample counterpart
        """
        if self.getRawSample():
            return False
        return True
