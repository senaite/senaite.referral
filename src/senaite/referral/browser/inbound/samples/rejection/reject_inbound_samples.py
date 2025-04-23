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

import six
from bika.lims import api
from bika.lims import senaiteMessageFactory as _
from plone.memoize import view
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from senaite.core import logger
from senaite.core.api.dtime import to_localized_time
from senaite.referral.catalog import INBOUND_SAMPLE_CATALOG


class RejectInboundSamplesView(BrowserView):
    """View that renders the Inbound Samples rejection view
    """
    template = ViewPageTemplateFile("templates/reject_inbound_samples.pt")

    def __init__(self, context, request):
        super(RejectInboundSamplesView, self).__init__(context, request)
        self.context = context
        self.request = request
        self.back_url = self.context.absolute_url()

    def __call__(self):
        form = self.request.form

        # Form submit toggle
        form_submitted = form.get("submitted", False)

        # Buttons
        form_continue = form.get("button_continue", False)
        form_cancel = form.get("button_cancel", False)

        # Get the objects from request
        inbound_samples = self.get_inbound_samples_from_request()

        # No Inbound Samples selected
        if not inbound_samples:
            return self.redirect(message=_("No items selected"),
                                 level="warning")

        # Handle rejection
        if form_submitted and form_continue:
            logger.info("*** REJECT INBOUND SAMPLES ***")
            processed = []
            for inbound_sample in form.get("inbound_samples", []):
                inbound_sample_uid = inbound_sample.get("uid", "")
                reasons = inbound_sample.get("reasons", [])
                other = inbound_sample.get("other_reasons", "")
                if not inbound_sample_uid:
                    continue

                # Omit if no rejection reason specified
                if not any([reasons, other]):
                    continue

                # This is quite bizarre!
                # AR's Rejection reasons is a RecordsField, but with one
                # record only, that contains both predefined and other reasons.
                obj = api.get_object_by_uid(inbound_sample_uid)
                rejection_reasons = {
                    "other": other,
                    "selected": reasons
                }
                obj.setRejectionReasons([rejection_reasons])

                # Reject the sample
                processed.append(obj)

            if not processed:
                return self.redirect(message=_("No samples were rejected"))

            message = _("Rejected {} samples: {}").format(
                len(processed), ", ".join(map(api.get_id, processed)))
            return self.redirect(message=message)

        # Handle cancel
        if form_submitted and form_cancel:
            logger.info("*** CANCEL REJECTION ***")
            return self.redirect(message=_("Rejection cancelled"))

        return self.template()

    @view.memoize
    def get_inbound_samples_from_request(self):
        """Returns a list of objects coming from the "uids" request parameter
        """
        uids = self.request.form.get("uids", "")
        if isinstance(uids, six.string_types):
            uids = uids.split(",")

        uids = list(set(uids))
        if not uids:
            return []

        inbound_samples = []
        query = dict(portal_type="InboundSample", UID=uids)
        for brain in api.search(query, INBOUND_SAMPLE_CATALOG):
            inbound_sample = api.get_object(brain)
            inbound_samples.append(inbound_sample)
        return inbound_samples

    @view.memoize
    def get_rejection_reasons(self):
        """Returns the list of available rejection reasons
        """
        return api.get_setup().getRejectionReasonsItems()

    def get_inbound_samples_data(self):
        """Returns a list of Inbound Samples data (dictionary)
        """
        for obj in self.get_inbound_samples_from_request():
            yield {
                "obj": obj,
                "id": api.get_id(obj),
                "uid": api.get_uid(obj),
                "title": obj.Title(),
                "sample_type": obj.getSampleType(),
                "analyses": obj.getAnalyses(),
                "date": to_localized_time(
                    obj.getDateSampled(), long_format=True
                ),
            }

    def redirect(self, redirect_url=None, message=None, level="info"):
        """Redirect with a message
        """
        if redirect_url is None:
            redirect_url = self.back_url
        if message is not None:
            self.add_status_message(message, level)
        return self.request.response.redirect(redirect_url)

    def add_status_message(self, message, level="info"):
        """Set a portal status message
        """
        return self.context.plone_utils.addPortalMessage(message, level)
