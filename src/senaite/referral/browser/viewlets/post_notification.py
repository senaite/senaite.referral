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

from plone.app.layout.viewlets import ViewletBase
from plone.memoize import view
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from senaite.referral import check_installed
from senaite.referral.interfaces import IInboundSampleShipment
from senaite.referral.notifications import get_last_post

from bika.lims import api


class PostNotificationViewlet(ViewletBase):
    """Viewlet that displays information about the POST notification about
    current object to a target laboratory
    """
    index = ViewPageTemplateFile("templates/post_notification.pt")

    @check_installed(False)
    def is_visible(self):
        """Returns whether the viewlet must be visible or not
        """
        if not api.is_object(self.context):
            return False

        elif IInboundSampleShipment.providedBy(self.context):
            # There is a InboundSampleShipment-specific viewlet that takes
            # the samples from the shipment into account already
            if self.is_error():
                return True

            samples = self.context.getSamples()
            posts = filter(None, [get_last_post(sample) for sample in samples])
            if not posts and self.get_notification():
                return True

        elif self.get_notification():
            return True

        return False

    @view.memoize
    def get_notification(self):
        return get_last_post(self.context)

    def is_error(self):
        post = self.get_notification()
        if not post:
            return False
        return not post.get("success", False)
