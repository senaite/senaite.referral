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

from plone.memoize import view
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from senaite.referral import messageFactory as _
from senaite.referral.browser import BaseView
from senaite.referral.interfaces import IOutboundSampleShipment
from senaite.referral.workflow import ship_sample

from bika.lims import api
from bika.lims.catalog import CATALOG_ANALYSIS_REQUEST_LISTING


class ShipSamplesView(BaseView):

    template = ViewPageTemplateFile("templates/ship_samples.pt")

    def __call__(self):
        form = self.request.form

        # Form submit toggle
        form_submitted = form.get("submitted", False)
        form_assign = form.get("button_assign", False)
        form_cancel = form.get("button_cancel", False)

        # Handle cancel
        if form_submitted and form_cancel:
            return self.redirect(message=_("Samples shipment cancelled"))

        # Get the shipment (either from context or request form)
        shipment = self.get_shipment()
        if form_submitted and form_assign and not shipment:
            return self.reload(message=_("No shipment selected"),
                               level="error")

        # Get the samples passed-in through the request as a list of UIDs
        samples = self.get_samples_data()
        if not samples:
            return self.redirect(message=_("No samples selected"),
                                 level="warning")

        if shipment:
            # Ship the samples
            for sample in samples:
                sample_obj = sample["obj"]
                ship_sample(sample_obj, shipment)

            titles = ", ".join(map(lambda samp: samp["title"], samples))
            message = _("Shipped {} samples: {}".format(len(samples), titles))
            self.redirect(message=message)

        return self.template()

    def get_shipment(self):
        if IOutboundSampleShipment.providedBy(self.context):
            return self.context

        # Extract the Shipment from the form
        form = self.request.form
        shipment_uid = form.get("shipment_uid")
        shipment = api.get_object(shipment_uid, default=None)
        if not IOutboundSampleShipment.providedBy(shipment):
            shipment = None

        return shipment

    @view.memoize
    def get_samples_data(self):
        """Returns a list of Samples data
        """
        uids = self.get_uids_from_request()
        query = {"portal_type": "AnalysisRequest", "UID": uids}
        brains = api.search(query, CATALOG_ANALYSIS_REQUEST_LISTING)
        return map(self.get_sample_data, brains)

    def get_sample_data(self, sample):
        """Returns a dict representation of the sample for easy handling
        """
        obj = api.get_object(sample)
        client = obj.getClient()
        date_sampled = obj.getDateSampled()
        date_received = obj.getDateReceived()
        return {
            "obj": obj,
            "id": api.get_id(obj),
            "uid": api.get_uid(obj),
            "title": api.get_title(obj),
            "path": api.get_path(obj),
            "url": api.get_url(obj),
            "sample_type": api.get_title(obj.getSampleType()),
            "client": api.get_title(client),
            "date_sampled": self.ulocalized_time(date_sampled, long_format=0),
            "date_received": self.ulocalized_time(date_received, long_format=0),
        }
