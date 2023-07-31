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
from senaite.app.listing import ListingView
from senaite.referral import messageFactory as _
from senaite.referral.catalog import SHIPMENT_CATALOG
from senaite.referral.notifications import get_last_post
from senaite.referral.notifications import is_error
from senaite.referral.utils import get_image_url
from senaite.referral.utils import translate as t

from bika.lims import api
from bika.lims.browser import ulocalized_time
from bika.lims.utils import get_image
from bika.lims.utils import get_link
from bika.lims.utils import get_link_for


class OutboundSampleShipmentFolderView(ListingView):
    """View that lists Outbound Sample Shipment objects
    """

    def __init__(self, context, request):
        super(OutboundSampleShipmentFolderView, self).__init__(context, request)

        self.title = _("Outbound sample shipments")
        self.icon = get_image_url("outbound_shipment_big.png")
        self.show_select_row = False
        self.show_select_column = True

        self.catalog = SHIPMENT_CATALOG

        self.contentFilter = {
            "portal_type": "OutboundSampleShipment",
            "sort_on": "created",
            "sort_order": "descending",
        }

        self.context_actions = {}

        self.columns = collections.OrderedDict((
            ("shipment_id", {
                "title": _("Shipment ID"),
            }),
            ("reference_laboratory", {
                "title": _("Reference Lab"),
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
            ("delivered", {
                "title": _("Delivered"),
            }),
            ("lost", {
                "title": _("Lost"),
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
                "title": _("Active"),
                "contentFilter": {
                    "review_state": ["preparation", "ready", "dispatched"]
                },
                "columns": self.columns.keys(),
            },
            {
                "id": "preparation",
                "title": _("Under preparation"),
                "contentFilter": {"review_state": "preparation"},
                "columns": self.columns.keys(),
            }, {
                "id": "ready",
                "title": _("Ready"),
                "contentFilter": {"review_state": "ready"},
                "columns": self.columns.keys(),
            }, {
                "id": "dispatched",
                "title": _("Dispatched"),
                "contentFilter": {"review_state": "dispatched"},
                "columns": self.columns.keys(),
            }, {
                "id": "delivered",
                "title": _("Delivered"),
                "contentFilter": {"review_state": "delivered"},
                "columns": self.columns.keys(),
            },  {
                "id": "lost",
                "title": _("Lost"),
                "contentFilter": {"review_state": "lost"},
                "columns": self.columns.keys(),
            },  {
                "id": "rejected",
                "title": _("Rejected"),
                "contentFilter": {"review_state": "rejected"},
                "columns": self.columns.keys(),
            },  {
                "id": "cancelled",
                "title": _("Cancelled"),
                "contentFilter": {"review_state": "cancelled"},
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

        reference = obj.getReferenceLaboratory()
        item["reference_laboratory"] = api.get_title(reference)
        item["replace"]["reference_laboratory"] = get_link_for(reference)

        lab_code = reference.getCode()
        lab_url = api.get_url(reference)
        item["lab_code"] = lab_code
        item["replace"]["lab_code"] = get_link(lab_url, value=lab_code)

        item["num_samples"] = len(obj.getRawSamples())
        item["created_by"] = self.get_creator_fullname(obj)

        # dispatched, received, rejected, cancelled
        dispatched = obj.getDispatchedDateTime()
        delivered = obj.getDeliveredDateTime()
        rejected = obj.getRejectedDateTime()
        lost = obj.getLostDateTime()
        cancelled = obj.getCancelledDateTime()
        item.update({
            "dispatched": self.get_localized_date(dispatched, show_time=True),
            "delivered": self.get_localized_date(delivered, show_time=True),
            "rejected": self.get_localized_date(rejected, show_time=True),
            "lost": self.get_localized_date(lost, show_time=True),
            "cancelled": self.get_localized_date(cancelled, show_time=True),
        })

        # If the notification errored, then add an icon
        post = get_last_post(obj)
        if not post:
            # Not notified to the reference lab
            msg = t(_("Reference lab not notified"))
            icon = get_image("warning.png", title=msg)
            self._append_html_element(item, "shipment_id", icon)

        elif is_error(post):
            # Notification to the reference lab errored
            msg = t(_("The notification to reference lab errored: {}"))
            message = "[{}] {}".format(post.get("status"), post.get("message"))
            msg = msg.format(message)

            icon = get_image("warning.png", title=msg)
            self._append_html_element(item, "shipment_id", icon)

        return item

    def _append_html_element(self, item, element, html, glue="&nbsp;",
                             after=True):
        """Appends an html value after or before the element in the item dict

        :param item: dictionary that represents an analysis row
        :param element: id of the element the html must be added thereafter
        :param html: element to append
        :param glue: glue to use for appending
        :param after: if the html content must be added after or before"""
        position = after and 'after' or 'before'
        item[position] = item.get(position, {})
        original = item[position].get(element, '')
        if not original:
            item[position][element] = html
            return
        item[position][element] = glue.join([original, html])

    def get_localized_date(self, date_value, show_time=1, default=""):
        if not date_value:
            return default
        return ulocalized_time(date_value, long_format=show_time)

    def get_creator_fullname(self, shipment):
        """Returns the fullname of the user who created the shipment
        """
        creator = shipment.Creator()
        properties = api.get_user_properties(creator)
        return properties.get("fullname", creator)
