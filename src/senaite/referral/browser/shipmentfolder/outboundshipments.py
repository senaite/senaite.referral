# -*- coding: utf-8 -*-

import collections
from plone.memoize import view
from senaite.core.listing import ListingView
from senaite.referral import messageFactory as _
from senaite.referral.utils import get_image_url

from bika.lims import api
from bika.lims.browser import ulocalized_time
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

        self.catalog = "portal_catalog"

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
                "title": _("Under preparation"),
                "contentFilter": {"review_state": "preparation"},
                "columns": self.columns.keys(),
            }, {
                "id": "undelivered",
                "title": _("Undelivered"),
                "contentFilter": {"review_state": "undelivered"},
                "columns": self.columns.keys(),
            }, {
                "id": "delivered",
                "title": _("Delivered"),
                "contentFilter": {"review_state": "rejected"},
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
        shipment_id = obj.get_shipment_id()
        item["shipment_id"] = shipment_id
        item["replace"]["shipment_id"] = get_link(href, shipment_id)

        reference = obj.get_reference_laboratory()
        reference = self.get_object(reference)
        item["reference_laboratory"] = api.get_title(reference)
        item["replace"]["reference_laboratory"] = get_link_for(reference)

        # dispatched, received, rejected, cancelled
        dispatched = obj.get_dispatched_datetime()
        delivered = obj.get_delivered_datetime()
        rejected = obj.get_rejected_datetime()
        lost = obj.get_lost_datetime()
        cancelled = obj.get_cancelled_datetime()
        item.update({
            "dispatched": self.get_localized_date(dispatched, show_time=True),
            "delivered": self.get_localized_date(delivered, show_time=True),
            "rejected": self.get_localized_date(rejected, show_time=True),
            "lost": self.get_localized_date(lost, show_time=True),
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
