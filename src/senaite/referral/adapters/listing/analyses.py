# -*- coding: utf-8 -*-

from senaite.core.listing.interfaces import IListingView
from senaite.core.listing.interfaces import IListingViewAdapter
from senaite.referral import check_installed
from senaite.referral import messageFactory as _
from zope.component import adapter
from zope.interface import implementer

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

        return item

    def get_reference_verifiers(self, analysis):
        """Returns a list with the names of the reference verifiers for the
        given analysis, with the reference laboratory code appended
        """
        verifiers = analysis.getReferenceVerifiers()
        verifiers = ["{} ({})".format(ref.get("fullname"), ref.get("lab_code"))
                     for ref in verifiers]
        return filter(None, verifiers)

    def is_referred(self, thing):
        """Returns whether the obj has been referred to another laboratory
        """
        if IAnalysisRequest.providedBy(thing):
            if thing.getOutboundShipment():
                return True
            return False

        elif IRequestAnalysis.providedBy(thing):
            sample = thing.getRequest()
            return self.is_referred(sample)
