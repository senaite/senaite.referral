# -*- coding: utf-8 -*-

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
    self.getField("OutboundShipment").set(self, obj)


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
