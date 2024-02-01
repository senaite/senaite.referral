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

from bika.lims import api
from bika.lims import PRIORITIES
from bika.lims.utils import get_image
from bika.lims.utils import get_link_for
from bika.lims.utils import render_html_attributes
from plone.memoize import view
from senaite.app.listing import ListingView
from senaite.core.api import dtime
from senaite.referral import messageFactory as _
from senaite.referral.catalog import INBOUND_SAMPLE_CATALOG
from senaite.referral.notifications import get_last_post
from senaite.referral.utils import get_image_url
from senaite.referral.utils import get_sample_types_mapping


class SamplesListingView(ListingView):
    """View that lists the Samples assigned to the current Shipment
    """
    def __init__(self, context, request):
        super(SamplesListingView, self).__init__(context, request)

        self.title = _("Samples")
        self.icon = get_image_url("shipment_samples_big.png")
        self.show_select_column = True

        self.catalog = INBOUND_SAMPLE_CATALOG
        self.contentFilter = {
            "portal_type": "InboundSample",
            "path": {
                "query": api.get_path(context),
                "level": 0
            },
            "sort_on": "created",
            "sort_order": "ascending"
        }

        self.context_actions = {}

        self.columns = collections.OrderedDict((
            ("priority", {
                "title": "",
                "sortable": False,
            }),
            ("getReferringID", {
                "title": _("Origin Sample ID"),
                "sortable": True,
            }),
            ("getSampleID", {
                "title": _("Local Sample ID"),
                "sortable": True,
            }),
            ("client", {
                "title": _("Client"),
                "sortable": False,
            }),
            ("sample_type", {
                "title": _("Sample Type"),
                "sortable": False,
            }),
            ("date_sampled", {
                "title": _("Sampled"),
                "sortable": False,
            }),
            ("analyses", {
                "title": _("Analyses"),
                "sortable": False,
            }),
            ("state_title", {
                "title": _("State"),
                "sortable": True,
                "index": "review_state"
            }),
        ))

        self.review_states = self.default_review_states

    @property
    def default_review_states(self):
        """Returns the default review states filter
        """
        print_stickers = {
            "id": "print_stickers",
            "title": _("Print stickers"),
            "url": "workflow_action?action=print_stickers"
        }
        review_states = [
            {
                "id": "received",
                "title": _("Received"),
                "contentFilter": {
                    "review_state": "received",
                },
                "custom_transitions": [print_stickers],
                "columns": self.columns.keys(),
            }, {
                "id": "rejected",
                "title": _("Rejected"),
                "contentFilter": {
                    "review_state": "rejected",
                },
                "custom_transitions": [],
                "columns": self.columns.keys(),
            }, {
                "id": "all",
                "title": _("All"),
                "contentFilter": {},
                "custom_transitions": [],
                "columns": self.columns.keys(),
            },
        ]
        return review_states

    def update(self):
        """Update hook
        """
        super(SamplesListingView, self).update()

        # Update states filter in accordance of shipment's current status
        self.update_review_states()

    def update_review_states(self):
        """Updates the states filter to match with shipment's current status
        """
        self.review_states = self.default_review_states
        context_status = api.get_review_status(self.context)
        if context_status == "received":
            # Default filter is received
            self.review_states[0]["id"] = "default"

        elif context_status == "rejected":
            # Default filter is rejected
            self.review_states[1]["id"] = "default"

            # selection of samples is not permitted
            self.show_select_column = False

        elif context_status == "due":
            # Insert a default "due" filter
            due = {
                "id": "default",
                "title": _("Due"),
                "contentFilter": {
                    "review_state": "due",
                },
                "columns": self.columns.keys(),
            }
            self.review_states.insert(0, due)
        else:
            # Default filter is "all"
            self.review_states[-1]["id"] = "default"

    def before_render(self):
        """Before template render hook
        """
        super(SamplesListingView, self).before_render()

    def folderitem(self, obj, item, index):
        obj = api.get_object(obj)
        sample = obj.getSample()
        if api.is_object(sample):
            # There is a sample counterpart for this inbound sample
            date_sampled = sample.getDateSampled()
            sample_type = sample.getSampleType()
            client = sample.getClient()
            analyses = map(lambda an: an.getKeyword, sample.getAnalyses())
            analyses = list(collections.OrderedDict.fromkeys(analyses))
            item.update({
                "uid": api.get_uid(sample),
                "getReferringID": obj.getReferringID(),
                "getSampleID": api.get_id(sample),
                "client": api.get_title(client),
                "priority": sample.getPriority(),
                "sample_type": api.get_id(sample_type),
                "date_sampled": date_sampled.strftime("%Y-%m-%d"),
                "analyses": ", ".join(analyses),
            })

            st_link = get_link_for(sample_type)
            original_st = obj.getSampleType()
            if original_st:
                st_link = "{} &rarr; {}".format(original_st, st_link)

            item["replace"]["getSampleID"] = get_link_for(sample)
            item["replace"]["sample_type"] = st_link
            item["replace"]["client"] = get_link_for(client)
            item["replace"]["state_title"] = self.get_state_title(sample)

            # Add an icon if last POST notification for this Sample failed
            if self.is_failed_notification(sample):
                msg = _("Notification to remote lab failed")
                img = get_image("exclamation.png", title=msg)
                item["after"]["sample_id"] = img

        else:
            # This inbound sample does not have a sample counterpart yet
            date_sampled = obj.getDateSampled()
            sample_type = obj.getSampleType()
            if not self.get_sample_type_uid(sample_type):
                msg = _("No sample type found for '{}'".format(sample_type))
                span = self.get_danger_html(sample_type, msg)
                item["replace"]["sample_type"] = span

            item.update({
                "getReferringID": obj.getReferringID(),
                "getSampleID": "",
                "client": "",
                "priority": obj.getPriority(),
                "sample_type": sample_type,
                "date_sampled": dtime.date_to_string(date_sampled),
                "analyses": ", ".join(obj.getAnalyses()),
            })

        priority = item.get("priority")
        if priority:
            priority_text = PRIORITIES.getValue(priority)
            priority_div = """<div class="priority-ico priority-{}">
                              <span class="notext">{}</span><div>
                           """
            priority = priority_div.format(priority, priority_text)
            item["replace"]["priority"] = priority

        return item

    def get_danger_html(self, text, title):
        """Returns an html with the text and title provided
        """
        css = "fas fa-exclamation-circle pr-1"
        attrs = render_html_attributes(title=title, css_class=css)
        return "<span class='text-danger'><i {}></i>{}".format(attrs, text)

    def get_state_title(self, obj):
        """Translates the review state to the current set language
        :param state: Review state title
        :type state: basestring
        :returns: Translated review state title
        """
        state = api.get_review_status(obj)
        ts = api.get_tool("translation_service")
        wf = api.get_tool("portal_workflow")
        portal_type = api.get_portal_type(obj)
        state_title = wf.getTitleForStateOnType(state, portal_type)
        return ts.translate(_(state_title or state), context=self.request)

    def is_failed_notification(self, obj):
        """Returns whether the last notification POST for the given object
        failed or not
        """
        post = get_last_post(obj)
        if not post:
            return False
        success = post.get("success", False)
        return not success

    @view.memoize
    def get_sample_types(self):
        """Returns the available sample type uids grouped by multiple terms
        """
        return get_sample_types_mapping()

    def get_sample_type_uid(self, term):
        """Returns the UID of the Sample Type that matches with the given term,
        if any. Returns None otherwise
        """
        sample_types = self.get_sample_types()
        return sample_types.get(term)
