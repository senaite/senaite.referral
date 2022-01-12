# -*- coding: utf-8 -*-

from plone.memoize import view
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from senaite.referral import messageFactory as _
from senaite.referral.browser import BaseView
from senaite.referral.interfaces import IOutboundSampleShipment

from bika.lims import api
from bika.lims.catalog import CATALOG_ANALYSIS_REQUEST_LISTING
from bika.lims.workflow import doActionFor


class ShipSamplesView(BaseView):

    template = ViewPageTemplateFile("templates/ship_samples.pt")

    def __call__(self):
        form = self.request.form

        # Form submit toggle
        form_submitted = form.get("submitted", False)
        form_assign = form.get("button_assign", False)
        form_create = form.get("button_create", False)
        form_cancel = form.get("button_cancel", False)

        # Get the samples passed-in through the request as a list of UIDs
        samples = self.get_samples_data()
        if not samples:
            return self.redirect(message=_("No samples selected"),
                                 level="warning")

        # Handle shipment
        if form_submitted:

            shipment_uid = None
            if form_assign:
                # Assign samples to selected shipment
                shipment_uid = form.get("shipment_uid")

            obj = api.get_object(shipment_uid, default=None)
            if not IOutboundSampleShipment.providedBy(obj):
                return self.reload(message=_("No shipment selected"),
                                   level="error")

            # Assign the samples to the shipment
            for sample in samples:
                obj.add_sample(sample["uid"])
                doActionFor(sample["obj"], "ship")

            titles = ", ".join(map(lambda sample: sample["title"], samples))
            message = _("Shipped {} samples: {}".format(len(samples), titles))
            self.redirect(message=message)

        # Handle cancel
        if form_submitted and form_cancel:
            return self.redirect(message=_("Samples shipment cancelled"))

        return self.template()

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
