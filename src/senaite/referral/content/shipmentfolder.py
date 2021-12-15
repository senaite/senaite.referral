# -*- coding: utf-8 -*-

from plone.dexterity.content import Container
from senaite.referral.interfaces import IShipmentFolder
from zope.interface import implementer


@implementer(IShipmentFolder)
class ShipmentFolder(Container):
    """'Fake' folder for the nav bar and used to display InboundSampleShipment
    and OutboundSampleShipment objects that actually live inside
    ExternalLaboratory objects
    """
    # Catalogs where this type will be catalogued
    _catalogs = ["uid_catalog", "portal_catalog"]
