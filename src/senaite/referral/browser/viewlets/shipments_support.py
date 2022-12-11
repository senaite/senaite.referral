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
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from senaite.referral import check_installed
from senaite.referral.utils import is_valid_url


class ShipmentsSupportViewlet(ViewletBase):
    """Viewlet that notifies the user that current external laboratory does not
    support the automatic submission of shipments
    """
    index = ViewPageTemplateFile("templates/shipments_support.pt")

    @check_installed(False)
    def is_visible(self):
        """Returns whether the viewlet must be visible or not
        """
        current_url = self.request.get("URL")
        if not current_url.endswith("outbound_shipments"):
            return False

        if not self.is_reference_lab():
            return True
        if not self.is_valid_lab_url():
            return True
        if not self.is_valid_credentials():
            return True
        return False

    def is_reference_lab(self):
        return self.context.getReference()

    def is_valid_lab_url(self):
        url = self.context.getUrl()
        return is_valid_url(url)

    def is_valid_credentials(self):
        username = self.context.getUsername()
        password = self.context.getPassword()
        return all([username, password])
