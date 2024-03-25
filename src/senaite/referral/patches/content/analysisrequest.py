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

from senaite.referral.interfaces import IInboundSampleShipment
from senaite.referral.interfaces import IOutboundSampleShipment

from bika.lims import api


def setInboundShipment(self, value):
    """Assigns an InboundSampleShipment to InboundShipment field
    """
    obj = api.get_object(value, default=None)
    if obj and not IInboundSampleShipment.providedBy(obj):
        raise ValueError("Type is not supported")
    self.getField("InboundShipment").set(self, obj)


def getInboundShipment(self):
    """Returns the InboundSampleShipment object the AnalysisRequest comes from
    if any. Returns None otherwise
    """
    obj = self.getField("InboundShipment").get(self)
    return api.get_object(obj, default=None)


def hasInboundShipment(self):
    """Returns whether the sample comes from an inbound sample shipment
    """
    uid = self.getField("InboundShipment").getRaw(self)
    return api.is_uid(uid)


def setOutboundShipment(self, value):
    """Assigns the value to OutboundShipment field
    """
    obj = api.get_object(value, default=None)
    if obj and not IOutboundSampleShipment.providedBy(obj):
        raise ValueError("Type is not supported")

    # check if the value changed
    import pdb;pdb.set_trace()
    old = self.getOutboundShipment()
    if old == obj:
        return

    # remove this sample from the old shipment
    if old:
        old.removeSample(self)

    # assign the shipment to the field
    self.getField("OutboundShipment").set(self, obj)

    # add this sample to the new shipment
    if obj:
        obj.addSample(self)


def getOutboundShipment(self):
    """Returns the Outbound Shipment object the AnalysisRequest is assigned to
    """
    obj = self.getField("OutboundShipment").get(self)
    return api.get_object(obj, default=None)


def hasOutboundShipment(self):
    """Returns whether the sample has been assigned to an Outbound shipment
    """
    uid = self.getField("OutboundShipment").getRaw(self)
    return api.is_uid(uid)


def getInboundSample(self):
    """Returns the Inbound Sample this sample was generated from, if any
    """
    # TODO 2.x Replace by get_backreferences
    shipment = self.getInboundShipment()
    if not shipment:
        return None

    uid = api.get_uid(self)
    for inbound_sample in shipment.getInboundSamples():
        if inbound_sample.getRawSample() == uid:
            return inbound_sample

    return None
