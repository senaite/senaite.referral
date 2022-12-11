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

from bika.lims import api
from plone.app.layout.viewlets import ViewletBase
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from senaite.referral import check_installed
from senaite.referral.utils import get_lab_code
from senaite.referral.utils import is_valid_url


class ReferralConfigurationViewlet(ViewletBase):
    """Viewlet that reminds user to review the configuration of senaite.referral
    """
    index = ViewPageTemplateFile("templates/configuration_viewlet.pt")

    @check_installed(False)
    def is_visible(self):
        """Returns whether the viewlet must be visible or not
        """
        code = get_lab_code()
        return not code

    def get_control_panel_url(self):
        """Returns the url to senaite.referral's control panel
        """
        portal = api.get_portal()
        portal_url = api.get_url(portal)
        authenticator = self.request.get("_authenticator")
        base_url = "{}/@@referral-controlpanel?_authenticator={}"
        return base_url.format(portal_url, authenticator)
