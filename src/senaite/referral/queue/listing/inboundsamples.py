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

from senaite.app.listing.interfaces import IListingView
from senaite.app.listing.interfaces import IListingViewAdapter
from senaite.queue import api as qapi
from senaite.queue import messageFactory as _q
from senaite.referral import check_installed
from zope.component import adapter
from zope.interface import implementer

from bika.lims import api


@adapter(IListingView)
@implementer(IListingViewAdapter)
class InboundSamplesListingAdapter(object):

    def __init__(self, listing, context):
        self.listing = listing
        self.context = context

    @check_installed(None)
    def before_render(self):
        if qapi.is_queued(self.context):
            self.listing.show_select_column = False

    @check_installed(None)
    def folder_item(self, obj, item, index):
        obj = api.get_object(obj)
        if qapi.is_queued(obj):
            item["disabled"] = True
            item["replace"]["state_title"] = _q("Queued")

        return item
