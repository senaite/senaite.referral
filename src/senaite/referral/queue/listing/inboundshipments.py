# -*- coding: utf-8 -*-

from senaite.core.listing.interfaces import IListingView
from senaite.core.listing.interfaces import IListingViewAdapter
from senaite.queue import api as qapi
from senaite.queue import messageFactory as _q
from senaite.referral import check_installed
from zope.component import adapter
from zope.interface import implementer

from bika.lims import api


@adapter(IListingView)
@implementer(IListingViewAdapter)
class InboundShipmentsListingAdapter(object):

    def __init__(self, listing, context):
        self.listing = listing
        self.context = context

    @check_installed(None)
    def before_render(self):
        pass

    @check_installed(None)
    def folder_item(self, obj, item, index):
        obj = api.get_object(obj)
        if qapi.is_queued(obj):
            item["disabled"] = True
            item["replace"]["state_title"] = _q("Queued")

        return item
