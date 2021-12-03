# -*- coding: utf-8 -*-

from plone.dexterity.content import Container
from senaite.referral.interfaces import IExternalLaboratoryFolder
from zope.interface import implementer


@implementer(IExternalLaboratoryFolder)
class ExternalLaboratoryFolder(Container):
    """Folder for ExternalLaboratory contents
    """
    # Catalogs where this type will be catalogued
    _catalogs = ["uid_catalog", "portal_catalog"]
