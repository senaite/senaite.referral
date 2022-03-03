# -*- coding: utf-8 -*-
import collections

from senaite.core.listing import utils as listing_utils
from senaite.core.listing.interfaces import IListingView
from senaite.core.listing.interfaces import IListingViewAdapter
from senaite.referral import messageFactory as _
from senaite.referral.utils import get_field_value
from zope.component import adapter
from zope.interface import implementer

from bika.lims import api
from bika.lims.utils import get_link_for


@adapter(IListingView)
@implementer(IListingViewAdapter)
class AnalysisRequestsListingViewAdapter(object):

    def __init__(self, listing, context):
        self.listing = listing
        self.context = context

    def before_render(self):
        # Additional columns
        self.add_columns()
        self.add_review_states()

    def folder_item(self, obj, item, index):
        obj = api.get_object(obj)

        # Outbound shipment
        outbound = get_field_value(obj, "OutboundShipment", default="")
        if outbound:
            link = get_link_for(outbound)
            ico = self.get_glyphicon("export")
            item["replace"]["Shipment"] = "{}{}".format(ico, link)
            outbound = api.get_title(outbound)

        # Inbound shipment
        inbound = get_field_value(obj, "InboundShipment", default="")
        if inbound:
            link = get_link_for(inbound)
            ico = self.get_glyphicon("import")
            val = "{}{}".format(ico, link)
            if outbound:
                val = "&nbsp;|&nbsp;".join([val, item["replace"]["Shipment"]])
            item["replace"]["Shipment"] = val
            inbound = api.get_title(inbound)

        item["Shipment"] = "{} {}".format(outbound, inbound).strip()

        return item

    def get_glyphicon(self, name):
        """Returns an html element that represents the glyphicon with the name
        """
        span = '<span class="glyphicon glyphicon-{}" ' \
               'style="padding-right:3px"></span>'
        return span.format(name)

    def add_review_states(self):
        """Adds referral-specific review states (filter buttons) in the listing
        """
        # Use 'invalid' review state as the template
        invalid = filter(lambda o: o["id"] == "invalid",
                         self.listing.review_states)[0]
        default_columns = invalid.get("columns")
        default_actions = invalid.get("custom_transitions", [])

        # New review_state "shipped"
        shipped = {
            "id": "shipped",
            "title": _("Referred"),
            "contentFilter": {
                "review_state": ("shipped",),
                "sort_on": "created",
                "sort_order": "descending"},
            "transitions": [],
            "custom_transitions": list(default_actions),
            "columns": list(default_columns),
        }
        listing_utils.add_review_state(
            listing=self.listing,
            review_state=shipped,
            after="invalid")

    def add_columns(self):
        """Adds referral-specific columns in the listing
        """
        custom_columns = collections.OrderedDict((
            ("Shipment", {
                "title": _("Shipment"),
                "sortable": False,
                "toggle": True,
                "after": "getAnalysesNum",
            }),
        ))

        # Add the columns, but for "shipped" status only
        rv_keys = map(lambda r: r["id"], self.listing.review_states)
        for column_id, column_values in custom_columns.items():
            listing_utils.add_column(
                listing=self.listing,
                column_id=column_id,
                column_values=column_values,
                after=column_values.get("after", None),
                review_states=rv_keys)
