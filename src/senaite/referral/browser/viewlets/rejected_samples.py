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

from plone.app.layout.viewlets import ViewletBase
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from senaite.referral.interfaces import IInboundSampleShipment


class RejectedSamplesViewlet(ViewletBase):
    """Displays information about rejected inbound samples
    """
    template = ViewPageTemplateFile("templates/rejected_samples_viewlet.pt")

    def __init__(self, context, request, view, manager):
        super(RejectedSamplesViewlet, self).__init__(
            context, request, view, manager)
        self.context = context
        self.request = request
        self.view = view

    def index(self):
        if not IInboundSampleShipment.providedBy(self.context):
            return ""

        # Get rejected inbound samples
        rejected_samples = []
        for sample in self.context.getInboundSamples():
            if sample.isRejected():
                rejected_samples.append(sample)

        if not rejected_samples:
            return ""

        self.rejected_samples = rejected_samples
        return self.template()
