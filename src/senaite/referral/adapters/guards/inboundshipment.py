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
from bika.lims.workflow import isTransitionAllowed as is_transition_allowed


@implementer(IGuardAdapter)
class InboundShipmentGuardAdapter(BaseGuardAdapter):

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
                if inbound_sample.getRawSample():
                    continue
            if not is_transition_allowed(inbound_sample, action_id):
                return False
        return True
