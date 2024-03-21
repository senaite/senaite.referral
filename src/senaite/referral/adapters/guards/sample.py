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

from bika.lims import api
from bika.lims.interfaces import IGuardAdapter
from senaite.referral.adapters.guards import BaseGuardAdapter
from zope.interface import implementer


@implementer(IGuardAdapter)
class SampleGuardAdapter(BaseGuardAdapter):
    """Adapter for Sample guards
    """

    def guard_cancel(self):
        """Returns true if the sample was not created from a Sample Shipment
        """
        if self.context.hasInboundShipment():
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

    def guard_reject_at_reference(self):
        """Returns true if the sample can be transitioned to rejected at
        reference sample
        """
        # Do not allow to reject unless a POST from remote lab
        request = api.get_request()
        lab_code = request.get("lab_code")
        if not lab_code:
            return False

        return True

    def guard_invalidate_at_reference(self):
        """Returns true if current request contains a POST with the
        'invalidate_at_reference' action to ensure this transition is not
        performed manually,
        """
        request = api.get_request()
        lab_code = request.get("lab_code")
        if not lab_code:
            return False
        return True
