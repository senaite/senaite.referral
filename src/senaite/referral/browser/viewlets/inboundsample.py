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
# Copyright 2021-2025 by it's authors.
# Some rights reserved, see README and LICENSE.

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from bika.lims import api
from plone.app.layout.viewlets import ViewletBase
from plone.memoize import view
from senaite.referral import check_installed
from senaite.referral.catalog import INBOUND_SAMPLE_CATALOG


class RejectedInboundSamplesViewlet(ViewletBase):
    """Current Inbound Samples were rejected. Display the reasons
    """
    template = ViewPageTemplateFile("templates/rejected_inbound_samples_viewlet.pt")  # noqa: E501

    @check_installed(False)
    def is_visible(self):
        """Returns whether the viewlet must be visible or not
        """
        rejected_inbound_samples = self.get_rejected_inbound_samples()
        if not rejected_inbound_samples:
            return False

        return True

    def get_rejected_inbound_samples(self):
        """Returns the rejected inbound samples
        """
        query = dict(
            portal_type="InboundSample",
            path=dict(query=api.get_path(self.context), level=0),
            review_state="rejected")
        brains = api.search(query, INBOUND_SAMPLE_CATALOG)
        return [api.get_object(brain) for brain in brains]

    @view.memoize
    def has_reasons(self, inbound_sample):
        """Returns whether the sample has reasons or not
        """
        return (
            inbound_sample.getSelectedRejectionReasons() or
            inbound_sample.getOtherRejectionReasons()
        )
