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
from bika.lims import AddAnalysisRequest
from bika.lims import api
from bika.lims import bikaMessageFactory as _c
from bika.lims import PRIORITIES
from bika.lims.api.security import check_permission
from senaite.core.catalog import SAMPLE_CATALOG
from senaite.referral import messageFactory as _
from senaite.app.listing import ListingView
from senaite.referral.utils import get_image_url


class AddSamplesListingView(ListingView):
    """View that lists the Samples available for assignment to current shipment
    """

    def __init__(self, context, request):
        super(AddSamplesListingView, self).__init__(context, request)

        self.title = _("Add samples")
        self.description = _(
            "Create and add a new sample to this shipment or select existing "
            "samples you wish to add"
        )
        self.icon = get_image_url("shipment_samples_big.png")
        self.show_select_column = True
        self.show_select_all_checkbox = True
        self.show_search = True

        self.catalog = SAMPLE_CATALOG
        self.contentFilter = {
            "review_state": "sample_received",
            "assigned_state": "unassigned",
            "sort_on": "created",
            "sort_order": "descending",
            "isRootAncestor": True
        }

        self.columns = collections.OrderedDict((
            ("priority", {
                "title": ""}),
            ("getId", {
                "title": _c("Sample ID"),
                "attr": "getId",
                "replace_url": "getURL",
                "index": "getId",
                "sortable": True}),
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
            ("state_title", {
                "title": _("State"),
                "sortable": True,
                "index": "review_state"}),
        ))

        self.review_states = [{
            "id": "default",
            "title": _("All samples"),
            "contentFilter": {},
            "transitions": [{
                "id": "ship",
                "url": "referral_ship_samples",
            }],
            "columns": self.columns.keys(),
        }]

        self.context_actions = {}

    def update(self):
        """Called before the listing renders
        """
        super(AddSamplesListingView, self).update()

        samples_folder = api.get_portal().samples
        if check_permission(AddAnalysisRequest, samples_folder):
            uid = api.get_uid(self.context)
            url = api.get_url(samples_folder)
            url = "{}/ar_add?ar_count=1&OutboundShipment={}".format(url, uid)

            self.context_actions.update({
                _("Add new sample"): {
                    "url": url,
                    "icon": "++resource++bika.lims.images/add.png"
                }
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
