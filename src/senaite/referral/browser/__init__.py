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

import six
from Products.Five.browser import BrowserView

from bika.lims import api
from bika.lims.browser import ulocalized_time


class BaseView(BrowserView):
    """Vitaminized Browser View
    """

    def __init__(self, context, request):
        super(BaseView, self).__init__(context, request)
        self.back_url = self.context.absolute_url()

    @property
    def current_url(self):
        """Return the current url
        """
        url = api.get_url(self.context)
        request_url = self.request.get("URL")
        parts = request_url.split("/")
        if parts:
            action = parts[-1]
            if not url.endswith(action):
                url = "{}/{}".format(url, action)

        query = self.request.get("QUERY_STRING", "")
        if query:
            query = "?{}".format(query)
        return "{}{}".format(url, query)

    def get_uids_from_request(self):
        """Return a list of uids from the request
        """
        uids = self.request.form.get("uids", "")
        if not uids:
            uids = self.request.get("uids", "")

        if isinstance(uids, six.string_types):
            uids = uids.split(",")
        unique_uids = collections.OrderedDict().fromkeys(uids).keys()
        return filter(api.is_uid, unique_uids)

    def redirect(self, redirect_url=None, message=None, level="info"):
        """Redirect with a message
        """
        if redirect_url is None:
            redirect_url = self.back_url
        if message is not None:
            self.add_status_message(message, level)
        return self.request.response.redirect(redirect_url)

    def reload(self, message=None, level="info"):
        """Redirect to current page with a message
        """
        return self.redirect(redirect_url=self.current_url, message=message,
                             level=level)

    def add_status_message(self, message, level="info"):
        """Set a portal status message
        """
        return self.context.plone_utils.addPortalMessage(message, level)

    def ulocalized_time(self, time, long_format=None, time_only=None):
        return ulocalized_time(time, long_format, time_only,
                               context=self.context, request=self.request)
