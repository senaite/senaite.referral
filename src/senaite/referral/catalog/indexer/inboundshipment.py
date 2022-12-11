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


@indexer(IInboundSampleShipment, IShipmentCatalog)
def shipment_searchable_text(instance):
    """Index for searchable text queries
    """
    laboratory = instance.getReferringLaboratory()
    searchable_text_tokens = [
        laboratory.getCode(),
        api.get_title(laboratory),
        # id of the inbound shipment
        api.get_id(instance),
        # original ID provided by the referring laboratory
        instance.getShipmentID(),
    ]
    searchable_text_tokens = filter(None, searchable_text_tokens)
    return u" ".join(searchable_text_tokens)
