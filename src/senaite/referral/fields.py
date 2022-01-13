# -*- coding: utf-8 -*-

from bika.lims.browser.fields import UIDReferenceField
from bika.lims.fields import ExtensionField


class ExtUIDReferenceField(ExtensionField, UIDReferenceField):
    """Field extender for UIDReferenceField
    """
    pass
