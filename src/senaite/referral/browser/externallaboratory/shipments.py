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
