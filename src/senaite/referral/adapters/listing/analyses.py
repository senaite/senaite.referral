# -*- coding: utf-8 -*-

from senaite.core.listing.interfaces import IListingView
from senaite.core.listing.interfaces import IListingViewAdapter
from senaite.referral import check_installed
from zope.component import adapter
from zope.interface import implementer


@adapter(IListingView)
@implementer(IListingViewAdapter)
class SampleAnalysesListingAdapter(object):
    """Adapter for analyses listings
    """

    # Priority order of this adapter over others
    priority_order = 99999

    def __init__(self, listing, context):
        self.listing = listing
        self.context = context

    @check_installed(None)
    def before_render(self):
        # Modify "Valid" filter to include "referred" analyses
        for rv in self.listing.review_states:
            if rv["id"] != "default":
                continue

            if "referred" in rv["contentFilter"]["review_state"]:
                continue

            rv["contentFilter"]["review_state"].append("referred")

    @check_installed(None)
    def folder_item(self, obj, item, index):
        return item
