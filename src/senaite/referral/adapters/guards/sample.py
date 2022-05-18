# -*- coding: utf-8 -*-
from senaite.referral.adapters.guards import BaseGuardAdapter
from zope.interface import implementer

from bika.lims import api
from bika.lims.interfaces import IGuardAdapter


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
