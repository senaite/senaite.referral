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

from senaite.core.listing.interfaces import IListingView
from senaite.core.listing.interfaces import IListingViewAdapter
from senaite.referral import check_installed
from senaite.referral import messageFactory as _
from senaite.referral.utils import get_services_mapping
from zope.component import adapter
from zope.interface import implementer

from bika.lims import api
from bika.lims.interfaces import IAnalysisRequest
from bika.lims.interfaces.analysis import IRequestAnalysis
from bika.lims.utils import get_image
from bika.lims.utils import t


@adapter(IListingView)
@implementer(IListingViewAdapter)
class SampleAnalysesListingAdapter(object):
    """Adapter for analyses listings
    """

    # Priority order of this adapter over others
    priority_order = 99999

    def __init__(self, listing, context):
        self.listing = listing
        self.context = context

    @check_installed(None)
    def before_render(self):
        # Modify "Valid" filter to include "referred" analyses
        for rv in self.listing.review_states:
            if rv["id"] != "default":
                continue

            if "referred" in rv["contentFilter"]["review_state"]:
                continue

            rv["contentFilter"]["review_state"].append("referred")

    @check_installed(None)
    def folder_item(self, obj, item, index):
        analysis = self.listing.get_object(obj)
        if self.is_referred(analysis):
            # Display empty in "Analyst" and "Submitter" columns
            item["replace"].update({
                "Analyst": " ",
                "SubmittedBy": " ",
            })

            # Display the reference lab verifiers instead of local
            verifiers = self.get_reference_verifiers(analysis)
            if verifiers:
                msg = t(_("Verified by reference lab: {}"))
                verifiers = ", ".join(verifiers)
                icon = get_image('warning.png', title=msg.format(verifiers))
                self.listing._append_html_element(item, 'state_title', icon)

            # Display the reference lab analysts instead of local
            analysts = self.get_reference_analysts(analysis)
            item["replace"]["Analyst"] = ", ".join(analysts)

            # Display the instrument of the ref lab
            instrument = analysis.getReferenceInstrument() or ""
            item["replace"]["Instrument"] = instrument

            # Display the method of the ref lab
            method = analysis.getReferenceMethod() or ""
            item["replace"]["Method"] = method

            if any([instrument, method]):
                # Tell the listing to display the instrument/method columns
                self.listing.show_methodinstr_columns = True

        return item

    def get_reference_analysts(self, analysis):
        """Returns a list with the names of the reference verifiers for the
        given analysis, with the reference laboratory code appended
        """
        analysts = analysis.getReferenceAnalysts()
        return self.get_reference_actors(analysts)

    def get_reference_verifiers(self, analysis):
        """Returns a list with the names of the reference verifiers for the
        given analysis, with the reference laboratory code appended
        """
        verifiers = analysis.getReferenceVerifiers()
        return self.get_reference_actors(verifiers)

    def get_reference_actors(self, actors):
        """Returns a list with the names of the actors, with the reference
        laboratory code appended
        """
        actors = ["{} ({})".format(ref.get("fullname"), ref.get("lab_code"))
                  for ref in actors]
        return filter(None, actors)

    def is_referred(self, thing):
        """Returns whether the obj has been referred to another laboratory
        """
        if IAnalysisRequest.providedBy(thing):
            return thing.hasOutboundShipment()

        elif IRequestAnalysis.providedBy(thing):
            sample = thing.getRequest()
            return self.is_referred(sample)


@adapter(IListingView)
@implementer(IListingViewAdapter)
class SampleManageAnalysesListingAdapter(object):
    """Adapter for manage analyses listings
    """

    # Priority order of this adapter over others
    priority_order = 99999

    _referring_services = None

    def __init__(self, listing, context):
        self.listing = listing
        self.context = context

    @property
    def referring_services(self):
        """Returns the UIDs of the services initially requested by the
        referring laboratory, if any
        """
        if self._referring_services is None:
            inbound_sample = self.context.getInboundSample()
            if not inbound_sample:
                self._referring_services = []
                return self._referring_services

            # Look up the uids of the requested services
            services = get_services_mapping()
            keywords = inbound_sample.getAnalyses() or []
            services_uids = map(lambda key: services.get(key), keywords)
            self._referring_services = filter(api.is_uid, services_uids)

        return self._referring_services

    @check_installed(None)
    def before_render(self):
        pass

    @check_installed(None)
    def folder_item(self, obj, item, index):
        # Skip services without analyses in the sample
        uid = api.get_uid(obj)
        if uid not in self.listing.analyses:
            return item

        if uid in self.referring_services:
            # Mark the row as disabled as it was requested by referring lab
            item["disabled"] = True

        return item
