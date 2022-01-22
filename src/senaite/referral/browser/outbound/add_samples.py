# -*- coding: utf-8 -*-
from senaite.referral.browser.outbound.samples import SamplesListingView
from senaite.referral import messageFactory as _


class AddSamplesListingView(SamplesListingView):
    """View that lists the Samples available for assignment to current shipment
    """

    def __init__(self, context, request):
        super(AddSamplesListingView, self).__init__(context, request)

        self.title = _("Add samples")
        self.show_search = True

        self.contentFilter = {
            "review_state": "sample_received",
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

    def isItemAllowed(self, obj):
        # Do not render samples w/o analyses awaiting for submission
        analyses_num = obj.getAnalysesNum
        if not analyses_num[2]:
            return False
        return True
