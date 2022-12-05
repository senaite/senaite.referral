# -*- coding: utf-8 -*-

from plone.indexer import indexer
from senaite.referral.interfaces import IInboundSample

from bika.lims import api


@indexer(IInboundSample)
def date_sampled(instance):
    """Returns the date when the inbound sample was originally collected
    """
    return instance.getDateSampled()


@indexer(IInboundSample)
def laboratory_code(instance):
    """Returns the code of the lab referring the inbound sample
    """
    referring_laboratory = instance.getReferringLaboratory()
    return referring_laboratory.getCode()


@indexer(IInboundSample)
def laboratory_title(instance):
    """Returns the code of the lab referring the inbound sample
    """
    referring_laboratory = instance.getReferringLaboratory()
    return api.get_title(referring_laboratory)


@indexer(IInboundSample)
def laboratory_uid(instance):
    """Returns the UID of the lab referring the inbound sample
    """
    referring_laboratory = instance.getReferringLaboratory()
    return api.get_uid(referring_laboratory)


@indexer(IInboundSample)
def referring_id(instance):
    """Returns the id of the inbound sample provided by the referring laboratory
    """
    return instance.getReferringID()


@indexer(IInboundSample)
def sample_id(instance):
    """Returns the id of AnalysisRequest record created when the inbound sample
    was received in the current laboratory, if any

    If the instance has no available sample assigned, it returns a tuple with
    a None value. This allows searches for `MissingValue` entries too.
    """
    sample = instance.getSample()
    if sample:
        return (api.get_id(sample),)
    return (None, )


@indexer(IInboundSample)
def sample_uid(instance):
    """Returns the UID of AnalysisRequest record created when the inbound sample
    was received in the current laboratory, if any

    If the instance has no available sample assigned, it returns a tuple with
    a None value. This allows searches for `MissingValue` entries too.
    """
    uid = instance.getRawSample()
    if api.is_uid(uid):
        return (uid,)
    return (None, )


@indexer(IInboundSample)
def shipment_id(instance):
    """Returns the id of the shipment the inbound sample belongs to
    """
    shipment = instance.getInboundShipment()
    return api.get_id(shipment)


@indexer(IInboundSample)
def shipment_uid(instance):
    """Returns the id of the shipment the inbound sample belongs to
    """
    shipment = instance.getInboundShipment()
    return api.get_uid(shipment)


@indexer(IInboundSample)
def inbound_sample_searchable_text(instance):
    """Index for searchable text queries
    """
    laboratory = instance.getReferringLaboratory()
    sample = instance.getSample()
    if sample:
        sample = api.get_id(sample)

    searchable_text_tokens = [
        laboratory.getCode(),
        api.get_title(laboratory),
        shipment_id(instance),
        instance.getReferringID(),
        instance.getSampleType(),
        sample,
        " ".join(instance.getAnalyses()),
    ]
    searchable_text_tokens = filter(None, searchable_text_tokens)
    return u" ".join(searchable_text_tokens)
