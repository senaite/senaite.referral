# -*- coding: utf-8 -*-
from Products.CMFCore.permissions import ModifyPortalContent
from senaite.referral.browser.shipmentfolder.inboundshipments import \
    InboundSampleShipmentFolderView
from senaite.referral.browser.shipmentfolder.outboundshipments import \
    OutboundSampleShipmentFolderView

from bika.lims import api
from bika.lims import bikaMessageFactory as _sc


class InboundSampleShipmentsView(InboundSampleShipmentFolderView):
    """View that lists Inbound Sample Shipment objects
    """

    def __init__(self, context, request):
        super(InboundSampleShipmentsView, self).__init__(context, request)
        self.contentFilter.update({
            "path": {
                "query": api.get_path(context),
                "depth": 1
            }
        })
        self.context_actions = {
            _sc("Add"): {
                "url": "++add++InboundSampleShipment",
                "permission": ModifyPortalContent,
                "icon": "++resource++bika.lims.images/add.png"}
        }


class OutboundSampleShipmentsView(OutboundSampleShipmentFolderView):
    """View that lists Inbound Sample Shipment objects
    """

    def __init__(self, context, request):
        super(OutboundSampleShipmentsView, self).__init__(context, request)
        self.contentFilter.update({
            "path": {
                "query": api.get_path(context),
                "depth": 1
            }
        })
        self.context_actions = {
            _sc("Add"): {
                "url": "++add++OutboundSampleShipment",
                "permission": ModifyPortalContent,
                "icon": "++resource++bika.lims.images/add.png"}
        }
