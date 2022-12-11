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

from plone.indexer import indexer
from senaite.referral.interfaces import IInboundSample
from senaite.referral.interfaces import IInboundSampleCatalog

from bika.lims import api


@indexer(IInboundSample, IInboundSampleCatalog)
def date_sampled(instance):
    """Returns the date when the inbound sample was originally collected
    """
    return instance.getDateSampled()


@indexer(IInboundSample, IInboundSampleCatalog)
def laboratory_code(instance):
    """Returns the code of the lab referring the inbound sample
    """
    referring_laboratory = instance.getReferringLaboratory()
    return referring_laboratory.getCode()


@indexer(IInboundSample, IInboundSampleCatalog)
def laboratory_title(instance):
    """Returns the code of the lab referring the inbound sample
    """
    referring_laboratory = instance.getReferringLaboratory()
    return api.get_title(referring_laboratory)


@indexer(IInboundSample, IInboundSampleCatalog)
def laboratory_uid(instance):
    """Returns the UID of the lab referring the inbound sample
    """
    referring_laboratory = instance.getReferringLaboratory()
    return api.get_uid(referring_laboratory)


@indexer(IInboundSample, IInboundSampleCatalog)
def referring_id(instance):
    """Returns the id of the inbound sample provided by the referring laboratory
    """
    return instance.getReferringID()


@indexer(IInboundSample, IInboundSampleCatalog)
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


@indexer(IInboundSample, IInboundSampleCatalog)
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


@indexer(IInboundSample, IInboundSampleCatalog)
def shipment_id(instance):
    """Returns the id of the shipment the inbound sample belongs to
    """
    shipment = instance.getInboundShipment()
    return api.get_id(shipment)


@indexer(IInboundSample, IInboundSampleCatalog)
def shipment_uid(instance):
    """Returns the id of the shipment the inbound sample belongs to
    """
    shipment = instance.getInboundShipment()
    return api.get_uid(shipment)


@indexer(IInboundSample, IInboundSampleCatalog)
def inbound_sample_searchable_text(instance):
    """Index for searchable text queries
    """
    laboratory = instance.getReferringLaboratory()
    sample = instance.getSample()
    if sample:
        sample = api.get_id(sample)

    shipment = instance.getInboundShipment()
    searchable_text_tokens = [
        laboratory.getCode(),
        api.get_title(laboratory),
        # id of the inbound shipment the sample belongs to
        api.get_id(shipment),
        # original ID provided by the referring laboratory
        shipment.getShipmentID(),
        instance.getReferringID(),
        instance.getSampleType(),
        sample,
        " ".join(instance.getAnalyses()),
    ]
    searchable_text_tokens = filter(None, searchable_text_tokens)
    return u" ".join(searchable_text_tokens)
