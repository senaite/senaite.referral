# -*- coding: utf-8 -*-
from senaite.referral.adapters.guards import BaseGuardAdapter
from zope.interface import implementer

from bika.lims import api
from bika.lims.interfaces import IGuardAdapter
from bika.lims.interfaces.analysis import IRequestAnalysis


@implementer(IGuardAdapter)
class AnalysisGuardAdapter(BaseGuardAdapter):
    """Adapter for Analysis guards
    """

    def get_sample(self, analysis):
        """Returns the sample the analysis belongs to, if any
        """
        if not IRequestAnalysis.providedBy(analysis):
            return None
        sample = analysis.getRequest()
        return sample

    def guard_refer(self):
        """Returns true if the sample status is shipped
        """
        sample = self.get_sample(self.context)
        if sample:
            return api.get_review_status(sample) in ["shipped"]
        return False
