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

from senaite.queue import api as qapi
from senaite.referral.queue import is_under_consumption
from zope.interface import implementer

from bika.lims.interfaces import IGuardAdapter


@implementer(IGuardAdapter)
class InboundShipmentGuardAdapter(object):

    def __init__(self, context):
        self.context = context

    def guard(self, action):
        """Returns False if the inbound shipment, or any of its inbound samples
        is being processed by the queue
        """
        if is_under_consumption(self.context):
            # Let the consumer perform the transition if necessary
            return True

        # Check if the shipment is queued
        if qapi.is_queued(self.context):
            return False

        # Check whether the shipment contains queued samples
        for sample in self.context.getInboundSamples():
            if qapi.is_queued(sample):
                return False

        return True
