# -*- coding: utf-8 -*-

from App.class_init import InitializeClass
from senaite.referral.core.catalog.base_catalog import BaseCatalog
from senaite.referral.core.catalog.base_catalog import COLUMNS as BASE_COLUMNS
from senaite.referral.core.catalog.base_catalog import INDEXES as BASE_INDEXES
from senaite.referral.interfaces import IShipmentCatalog
from zope.interface import implementer


CATALOG_ID = "senaite_catalog_shipment"
CATALOG_TITLE = "Senaite Shipment Catalog"

INDEXES = BASE_INDEXES + [
    # id, indexed attribute, type
    ("laboratory_uid", "", "FieldIndex"),
    ("shipment_id", "", "FieldIndex"),
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
