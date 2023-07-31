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

from App.class_init import InitializeClass
from senaite.core.catalog.base_catalog import BaseCatalog
from senaite.core.catalog.base_catalog import COLUMNS as BASE_COLUMNS
from senaite.core.catalog.base_catalog import INDEXES as BASE_INDEXES
from senaite.referral.interfaces import IShipmentCatalog
from zope.interface import implementer


CATALOG_ID = "senaite_catalog_shipment"
CATALOG_TITLE = "Senaite Shipment Catalog"

INDEXES = BASE_INDEXES + [
    # id, indexed attribute, type
    ("laboratory_uid", "", "FieldIndex"),
    ("shipment_id", "", "FieldIndex"),
    ("shipment_searchable_text", "", "ZCTextIndex"),
    ("sortable_title", "", "FieldIndex"),
]

COLUMNS = BASE_COLUMNS + [
    # attribute name
    "laboratory_uid",
    "shipment_id",
]

TYPES = [
    # portal_type name
    "InboundSampleShipment",
    "OutboundSampleShipment",
]


@implementer(IShipmentCatalog)
class ShipmentCatalog(BaseCatalog):
    """Catalog for Shipment objects
    """
    def __init__(self):
        BaseCatalog.__init__(self, CATALOG_ID, title=CATALOG_TITLE)

    @property
    def mapped_catalog_types(self):
        return TYPES


InitializeClass(ShipmentCatalog)
