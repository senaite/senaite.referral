# -*- coding: utf-8 -*-

from Products.CMFCore.permissions import ModifyPortalContent
from senaite.referral.browser.shipmentfolder.inboundshipments import \
    InboundSampleShipmentFolderView
from senaite.referral.browser.shipmentfolder.outboundshipments import \
    OutboundSampleShipmentFolderView

from bika.lims import api
from bika.lims import bikaMessageFactory as _sc
from senaite.referral.utils import is_manual_inbound_shipment_permitted


# Columns to remove from the listing
DELETE_COLUMNS = [
    "lab_code",
    "referring_laboratory",
]


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

        self.context_actions = {}
        if is_manual_inbound_shipment_permitted():
            self.context_actions = {
                _sc("Add"): {
                    "url": "++add++InboundSampleShipment",
                    "permission": ModifyPortalContent,
                    "icon": "++resource++bika.lims.images/add.png"}
            }

        # Remove lab-specific columns
        delete_columns = ["lab_code", "referring_laboratory"]
        for column_id in delete_columns:
            del self.columns[column_id]

        col_keys = self.columns.keys()
        for review_state in self.review_states:
            review_state.update({"columns": col_keys})


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

        # Remove lab-specific columns
        delete_columns = ["lab_code", "reference_laboratory"]
        for column_id in delete_columns:
            del self.columns[column_id]

        col_keys = self.columns.keys()
        for review_state in self.review_states:
            review_state.update({"columns": col_keys})
