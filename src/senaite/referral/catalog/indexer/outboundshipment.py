# -*- coding: utf-8 -*-

from plone.indexer import indexer
from senaite.referral.interfaces import IOutboundSampleShipment
from senaite.referral.interfaces import IShipmentCatalog

from bika.lims import api


@indexer(IOutboundSampleShipment, IShipmentCatalog)
def laboratory_uid(instance):
    """Returns the UID of the destination laboratory for this shipment
    """
    referring_laboratory = instance.getReferenceLaboratory()
    return api.get_uid(referring_laboratory)


@indexer(IOutboundSampleShipment, IShipmentCatalog)
def shipment_id(instance):
    """Returns the unique identifier of this Outbound Shipment
    """
    return instance.getShipmentID()


@indexer(IOutboundSampleShipment, IShipmentCatalog)
def shipment_searchable_text(instance):
    """Index for searchable text queries
    """
    laboratory = instance.getReferenceLaboratory()
    searchable_text_tokens = [
        laboratory.getCode(),
        api.get_title(laboratory),
        api.get_id(instance),
    ]
    searchable_text_tokens = filter(None, searchable_text_tokens)
    return u" ".join(searchable_text_tokens)
