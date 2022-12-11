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
