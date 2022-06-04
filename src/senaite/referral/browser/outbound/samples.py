# -*- coding: utf-8 -*-

import collections

from senaite.core.listing import ListingView
from senaite.referral import messageFactory as _
from senaite.referral.utils import get_image_url

from bika.lims import api
from bika.lims import bikaMessageFactory as _c
from bika.lims import PRIORITIES
from bika.lims.catalog import CATALOG_ANALYSIS_REQUEST_LISTING


class SamplesListingView(ListingView):
    """View that lists the Samples assigned to the current Shipment
    """

    def __init__(self, context, request):
        super(SamplesListingView, self).__init__(context, request)

        self.title = _("Samples")
        self.icon = get_image_url("shipment_samples_big.png")
        self.show_select_column = True
        self.show_select_all_checkbox = True
        self.show_search = False

        self.catalog = CATALOG_ANALYSIS_REQUEST_LISTING
        self.contentFilter = {
            "UID": context.getRawSamples(),
            "sort_on": "sortable_title",
            "sort_order": "ascending"
        }

        self.columns = collections.OrderedDict((
            ("priority", {
               "title": ""}),
            ("getId", {
                "title": _c("Sample ID"),
                "attr": "getId",
                "replace_url": "getURL",
                "index": "getId"}),
            ("getDateSampled", {
                "title": _c("Date Sampled"),
                "toggle": True}),
            ("getDateReceived", {
                "title": _c("Date Received"),
                "toggle": True}),
            ("Client", {
                "title": _c("Client"),
                "index": "getClientTitle",
                "attr": "getClientTitle",
                "replace_url": "getClientURL",
                "toggle": True}),
            ("getClientReference", {
                "title": _c("Client Ref"),
                "sortable": True,
                "index": "getClientReference",
                "toggle": False}),
            ("getClientSampleID", {
                "title": _c("Client SID"),
                "toggle": False}),
            ("getSampleTypeTitle", {
                "title": _c("Sample Type"),
                "sortable": True,
                "toggle": True}),
        ))

        self.review_states = [{
            "id": "default",
            "title": _("All samples"),
            "contentFilter": {},
            "transitions": [],
            "custom_transitions": [{
                "id": "recover_from_shipment",
                "title": _("Recover"),
                "help": _("Recover selected samples from this shipment"),
                "url": "workflow_action?action=recover_from_shipment",
            }],
            "confirm_transitions": [
                "recover_from_shipment",
            ],
            "columns": self.columns.keys(),
        }]

    def update(self):
        """Before template render hook
        """
        super(SamplesListingView, self).update()

        # "Recover" action is only available when status is "preparation"
        open_status = ["preparation", ]
        status = api.get_review_status(self.context)
        if status not in open_status:
            self.show_select_all_checkbox = False
            self.show_select_column = False
            for rv in self.review_states:
                rv.update({
                    "custom_transitions": [],
                    "confirm_transitions": [],
                })

    def folderitem(self, obj, item, index):
        """Applies new properties to item that is currently being rendered as a
        row in the list
        """
        received = obj.getDateReceived
        sampled = obj.getDateSampled

        sample = api.get_object(obj)
        priority = sample.getPriority()
        if priority:
            priority_text = PRIORITIES.getValue(priority)
            priority_div = """<div class="priority-ico priority-{}">
                                  <span class="notext">{}</span><div>
                               """
            priority = priority_div.format(priority, priority_text)
            item["replace"]["priority"] = priority

        item["getDateReceived"] = self.ulocalized_time(received, long_format=1)
        item["getDateSampled"] = self.ulocalized_time(sampled, long_format=1)
        return item
