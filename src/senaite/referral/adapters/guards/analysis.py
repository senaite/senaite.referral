# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.REFERRAL.
#
# SENAITE.REFERRAL is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright 2021-2022 by it's authors.
# Some rights reserved, see README and LICENSE.

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
