# -*- coding: utf-8 -*-

from zope.component import adapts

from bika.lims import api
from bika.lims.interfaces import IGetDefaultFieldValueARAddHook


class OutboundShipmentDefaultFieldValue(object):
    """Adapter that returns the default value for field OutboundShipment
    """
    adapts(IGetDefaultFieldValueARAddHook)

    def __init__(self, request):
        self.request = request

    def __call__(self, context):
        uid = self.request.get("OutboundShipment")
        return api.get_object_by_uid(uid, default=None)
