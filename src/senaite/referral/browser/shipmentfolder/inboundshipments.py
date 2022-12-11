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

import collections
from plone.memoize import view
from senaite.core.listing import ListingView
from senaite.referral import messageFactory as _
from senaite.referral.catalog import SHIPMENT_CATALOG
from senaite.referral.utils import get_image_url

from bika.lims import api
from bika.lims.browser import ulocalized_time
from bika.lims.utils import get_link
from bika.lims.utils import get_link_for


class InboundSampleShipmentFolderView(ListingView):
    """View that lists Inbound Sample Shipment objects
    """

    def __init__(self, context, request):
        super(InboundSampleShipmentFolderView, self).__init__(context, request)

        self.title = _("Inbound sample shipments")
        self.icon = get_image_url("inbound_shipment_big.png")
        self.show_select_row = False

        # We do not want the user to transition inbound shipments directly!
        self.show_select_column = False

        self.catalog = SHIPMENT_CATALOG

        self.contentFilter = {
            "portal_type": "InboundSampleShipment",
            "sort_on": "created",
            "sort_order": "descending",
        }

        self.context_actions = {}

        self.columns = collections.OrderedDict((
            ("shipment_id", {
                "title": _("Shipment ID"),
            }),
            ("referring_laboratory", {
                "title": _("Referring Lab"),
            }),
            ("lab_code", {
                "title": _("Lab code"),
            }),
            ("num_samples", {
                "title": _("#Samples"),
            }),
            ("created_by", {
                "title": _("Created by"),
            }),
            ("created", {
                "title": _("Created"),
                "sortable": True,
                "index": "created",
            }),
            ("dispatched", {
                "title": _("Dispatched"),
            }),
            ("received", {
                "title": _("Received"),
            }),
            ("rejected", {
                "title": _("Rejected"),
            }),
            ("cancelled", {
                "title": _("Cancelled"),
            }),
            ("state_title", {
                "title": _("State"),
                "sortable": True,
                "index": "review_state"}),
        ))

        self.review_states = [
            {
                "id": "default",
                "title": _("Due"),
                "contentFilter": {"review_state": "due"},
                "columns": self.columns.keys(),
            }, {
                "id": "received",
                "title": _("Received"),
                "contentFilter": {"review_state": "received"},
                "columns": self.columns.keys(),
            }, {
                "id": "rejected",
                "title": _("Rejected"),
                "contentFilter": {"review_state": "rejected"},
                "columns": self.columns.keys(),
            }, {
                "id": "all",
                "title": _("All"),
                "contentFilter": {},
                "columns": self.columns.keys(),
            },
        ]

    def folderitem(self, obj, item, index):
        """Service triggered each time an item is iterated in folderitems.
        The use of this service prevents the extra-loops in child objects.
        :obj: the instance of the class to be foldered
        :item: dict containing the properties of the object to be used by
            the template
        :index: current index of the item
        """
        obj = api.get_object(obj)
        href = api.get_url(obj)
        shipment_id = obj.getShipmentID()
        item["shipment_id"] = shipment_id
        item["replace"]["shipment_id"] = get_link(href, shipment_id)
        item["num_samples"] = len(obj.getInboundSamples())
        item["created_by"] = self.get_creator_fullname(obj)

        referring = obj.getReferringLaboratory()
        item["referring_laboratory"] = api.get_title(referring)
        item["replace"]["referring_laboratory"] = get_link_for(referring)

        lab_code = referring.getCode()
        lab_url = api.get_url(referring)
        item["lab_code"] = lab_code
        item["replace"]["lab_code"] = get_link(lab_url, value=lab_code)

        # dispatched, received, rejected, cancelled
        dispatched = obj.getDispatchedDateTime()
        received = obj.getReceivedDateTime()
        rejected = obj.getRejectedDateTime()
        cancelled = obj.getCancelledDateTime()
        item.update({
            "dispatched": self.get_localized_date(dispatched, show_time=True),
            "received": self.get_localized_date(received, show_time=True),
            "rejected": self.get_localized_date(rejected, show_time=True),
            "cancelled": self.get_localized_date(cancelled, show_time=True),
        })
        return item

    def get_localized_date(self, date_value, show_time=1, default=""):
        if not date_value:
            return default
        return ulocalized_time(date_value, long_format=show_time)

    @view.memoize
    def get_object(self, uid):
        return api.get_object_by_uid(uid)

    def get_creator_fullname(self, shipment):
        """Returns the fullname of the user who created the shipment
        """
        creator = shipment.Creator()
        properties = api.get_user_properties(creator)
        return properties.get("fullname", creator)
