# -*- coding: utf-8 -*-

from plone.indexer import indexer
from senaite.referral.interfaces import IInboundSampleShipment
from senaite.referral.interfaces import IShipmentCatalog

from bika.lims import api


@indexer(IInboundSampleShipment, IShipmentCatalog)
def laboratory_uid(instance):
    """Returns the UID of the lab referring the inbound sample shipment
    """
    referring_laboratory = instance.getReferringLaboratory()
    return api.get_uid(referring_laboratory)


@indexer(IInboundSampleShipment, IShipmentCatalog)
def shipment_id(instance):
    """Returns the unique identifier provided by the referring laboratory for
    the inbound sample shipment
    """
    return instance.getShipmentID()
