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
from pkg_resources import resource_listdir
from senaite.core.listing import ListingView
from senaite.referral import messageFactory as _
from senaite.referral import PRODUCT_NAME

from bika.lims import api
from bika.lims.utils import get_link
from bika.lims.utils import get_link_for


class ExternalLaboratoryFolderView(ListingView):
    """View that lists the External Laboratories
    """

    def __init__(self, context, request):
        super(ExternalLaboratoryFolderView, self).__init__(context, request)

        self.title = api.get_title(self.context)
        self.description = api.get_description(self.context)
        self.icon = api.get_icon(self.context, html_tag=False)
        self.icon = self.icon.replace(".png", "_big.png")
        self.show_select_row = False
        self.show_select_column = False

        self.catalog = "portal_catalog"

        self.contentFilter = {
            "portal_type": "ExternalLaboratory",
            "sort_on": "sortable_title",
            "sort_order": "ascending",
        }

        self.context_actions = {
            _("Add"): {
                "url": "++add++ExternalLaboratory",
                "permission": "Add portal content",
                "icon": "++resource++bika.lims.images/add.png"}
        }

        self.columns = collections.OrderedDict((
            ("code", {
                "title": _("Code"),
            }),
            ("title", {
                "title": _("Laboratory name"),
                "index": "sortable_title",
            }),
            ("reference", {
                "title": _("Reference"),
            }),
            ("referring", {
                "title": _("Referring"),
            })
        ))

        self.review_states = [
            {
                "id": "default",
                "title": _("Active"),
                "contentFilter": {"is_active": True},
                "columns": self.columns.keys(),
            }, {
                "id": "inactive",
                "title": _("Inactive"),
                "contentFilter": {'is_active': False},
                "columns": self.columns.keys(),
            }, {
                "id": "all",
                "title": _("All"),
                "contentFilter": {},
                "columns": self.columns.keys(),
            },
        ]

    def before_render(self):
        """Before template render hook
        """
        # Don't allow any context actions
        self.request.set("disable_border", 1)

    def folderitem(self, obj, item, index):
        """Service triggered each time an item is iterated in folderitems.
        The use of this service prevents the extra-loops in child objects.
        :obj: the instance of the class to be foldered
        :item: dict containing the properties of the object to be used by
            the template
        :index: current index of the item
        """
        obj = api.get_object(obj)
        obj_url = api.get_url(obj)
        obj_link = get_link_for(obj)
        item["replace"]["title"] = obj_link

        code = obj.getCode()
        item["code"] = code
        item["replace"]["code"] = get_link(href=obj_url, value=code)

        item["reference"] = obj.getReference()
        item["referring"] = obj.getReferring()
        return item
