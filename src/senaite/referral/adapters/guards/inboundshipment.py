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
from bika.lims.workflow import isTransitionAllowed as is_transition_allowed
from senaite.referral.adapters.guards import BaseGuardAdapter
from zope.interface import implementer


@implementer(IGuardAdapter)
class InboundShipmentGuardAdapter(BaseGuardAdapter):

    def guard_receive_inbound_samples(self):
        """Returns true if the inbound shipment contains at least one sample
        that has not been received yet, although it can
        """
        action_id = "receive_inbound_sample"
        for inbound_sample in self.context.getInboundSamples():
            if inbound_sample.getRawSample():
                continue
            if is_transition_allowed(inbound_sample, action_id):
                return True
        return False

    def guard_receive_inbound_shipment(self):
        """Returns true if the inbound shipment contains inbound samples and
        none of them are reception due
        """
        samples = self.context.getInboundSamples()
        if not samples:
            return False

        for inbound_sample in samples:
            if inbound_sample.getRawSample():
                continue
            if api.get_review_status(inbound_sample) == "due":
                return False

        return True

    def guard_reject_inbound_shipment(self):
        """Returns true if the inbound shipment does not have any sample or
        none of them were received
        """
        for inbound_sample in self.context.getInboundSamples():
            if inbound_sample.getRawSample():
                return False
        return True
