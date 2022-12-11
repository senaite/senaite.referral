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

from senaite.referral import messageFactory as _
from senaite.referral.browser.outbound.samples import SamplesListingView

from bika.lims import AddAnalysisRequest
from bika.lims import api
from bika.lims.api.security import check_permission


class AddSamplesListingView(SamplesListingView):
    """View that lists the Samples available for assignment to current shipment
    """

    def __init__(self, context, request):
        super(AddSamplesListingView, self).__init__(context, request)

        self.title = _("Add samples")
        self.description = _(
            "Create and add a new sample to this shipment or select existing "
            "samples you wish to add"
        )
        self.show_search = True

        self.contentFilter = {
            "review_state": "sample_received",
            "assigned_state": "unassigned",
            "sort_on": "created",
            "sort_order": "descending",
            "isRootAncestor": True
        }

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

        samples_folder = api.get_portal().analysisrequests
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
